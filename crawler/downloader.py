import logging
import requests
import random
import urllib.parse
from datetime import datetime, timezone, timedelta
from dbmeta import Db, DbMeta
import pagedb

class HostTolerance:
    def __init__(self, host):
        self.host = host
        self.delay = 0
        self.register()

    def register(self):
        self.lastvisit = datetime.now(timezone.utc)
        self.readyat = self.lastvisit + timedelta(milliseconds=self.delay)

class Tolerance:
    def __init__(self):
        self.hosts = {}
        self.firstdelay = 500
        self.raisedelay = 1.6
        self.reducedelay = 0.95

    def ready(self, url):
        hostname = urllib.parse.urlparse(url).hostname
        if hostname not in self.hosts:
            return True
        else:
            return self.hosts[hostname].readyat < datetime.now(timezone.utc)

    def register(self, url):
        hostname = urllib.parse.urlparse(url).hostname
        if hostname not in self.hosts:
            self.hosts[hostname] = HostTolerance(hostname)
        else:
            self.hosts[hostname].register()

    def add_delay(self, url):
        hostname = urllib.parse.urlparse(url).hostname
        if hostname not in self.hosts:
            self.hosts[hostname] = HostTolerance(hostname)
        tolerance = self.hosts[hostname]
        if tolerance.delay < self.firstdelay:
            tolerance.delay = self.firstdelay
        else:
            tolerance.delay *= self.raisedelay
        logging.info(f"Set up delay {tolerance.delay} for {hostname}")

    def remove_delay(self, url):
        hostname = urllib.parse.urlparse(url).hostname
        if hostname not in self.hosts:
            self.hosts[hostname] = HostTolerance(hostname)
        tolerance = self.hosts[hostname]
        tolerance.delay *= self.reducedelay
        logging.info(f"Set down delay {tolerance.delay} for {hostname}")

class Policy:
    def __init__(self):
        self.tolerance = Tolerance()
        self.novelty = 0.5
        self.rules = {}
        self.common = self.reject

    def load(self, ypolicy):
        if 'novelty' in ypolicy:
            self.novelty = ypolicy['novelty']

    def ready(self, candidate):
        return self.tolerance.ready(candidate.url)

    def dispatch(self, downloader, candidate, response):
        self.tolerance.register(candidate.url)
        if response.status_code in self.rules:
            return self.rules[response.status_code](downloader, candidate, response)
        return self.common(downloader, candidate, response)

    def store(self, downloader, candidate, response):
        self.tolerance.remove_delay(candidate.url)
        return downloader.store(candidate, response)

    def reject(self, downloader, candidate, response):
        return downloader.reject(candidate, response)

    def retry(self, downloader, candidate, response):
        self.tolerance.add_delay(candidate.url)
        return downloader.retry(candidate, response)

    @classmethod
    def default(cls):
        policy = cls()
        policy.default = policy.reject
        policy.rules = { 200:policy.store, 429:policy.retry }
        return policy

    @classmethod
    def single(cls):
        single = cls()
        single.default = single.store
        single.rules = {}
        return single

class Response:
    def __init__(self, candidate, response, page):
        self.candidate = candidate
        self.response = response
        self.page = page

class Downloader:
    def __init__(self, crawler, policy):
        self.crawler = crawler
        self.policy = policy

    def get_candidate(self):
        candidate = None
        for wu in DbMeta.getlist(self.crawler.indexdb, pagedb.WaitingUrl, "1=1 ORDER BY refcount*weight DESC, seqno"):
            candidate = wu
            if random.random() > self.policy.novelty and self.policy.ready(candidate):
                break
        return candidate

    def make_request(self, url):
        print(f'Getting {url}')
        headers = self.crawler.headers.copy()
        headers['host'] = urllib.parse.urlparse(url).hostname
        params = {}
        response = requests.request('GET', url, headers=headers, params=params, allow_redirects=False)
        logging.info(f"Url {url}: get {response.status_code} of {response.headers['Content-Type']}")
        return response

    def download(self):
        candidate = self.get_candidate()
        if candidate == None:
            return None
        logging.info(f'Url {candidate.url} was selected for downloading')
        response = self.make_request(candidate.url)
        return self.policy.dispatch(self, candidate, response)

    def store(self, candidate, response):
        offset = self.crawler.pager.store(response.content)
        page = pagedb.Page.create(self.crawler.indexdb, candidate.url, datetime.now(timezone.utc), response.status_code, response.headers['Content-Type'],
                                  offset, len(response.content))
        page.insert(self.crawler.indexdb)
        candidate.delete(self.crawler.indexdb)
        self.crawler.indexdb.finish()
        return Response(candidate, response, page)

    def reject(self, candidate, response):
        candidate.delete(self.crawler.indexdb)
        self.crawler.indexdb.finish()
        return Response(candidate, response, None)

    def retry(self, candidate, response):
        return Response(candidate, response, None)

    def load(self, ypolicy):
        self.policy.load(ypolicy)
