import logging
import yaml
import sys
import os
import random
from urllib.parse import urlparse
from datetime import datetime, timezone
import requests
sys.path.append(os.path.expanduser('~/dev/pydma'))
from dbmeta import Db, DbMeta
import pagedb

class Downloader:
    def __init__(self, crawler):
        self.crawler = crawler

    def get_candidate(self):
        for wu in DbMeta.getlist(self.crawler.indexdb, pagedb.WaitingUrl, "1=1 ORDER BY refcount*weight DESC, seqno"):
            if random.random() < 2:
                return wu
        return None

    def make_request(self, url):
        headers = self.crawler.headers.copy()
        headers['host'] = urlparse(url).hostname
        params = {}
        response = requests.request('GET', url, headers=headers, params=params, allow_redirects=False)
        print(f"Get {response.status_code} of {response.headers['Content-Type']} for {url}")
        return response

    def download(self):
        candidate = self.get_candidate()
        if candidate == None:
            return None
        response = self.make_request(candidate.url)
        offset = self.crawler.pager.store(response.content)
        page = pagedb.Page.create(self.crawler.indexdb, candidate.url, datetime.now(timezone.utc), response.status_code, response.headers['Content-Type'],
                                  offset, len(response.content))
        candidate.delete(self.crawler.indexdb)
        self.crawler.indexdb.finish()
        return page

class Pager:
    def __init__(self, crawler):
        self.crawler = crawler
        self.pages = None

    def open(self):
        self.pages = open(self.crawler.datafile, 'a+b')

    def close(self):
        self.pages.close()
        self.pages = None

    def store(self, content):
        self.pages.seek(0, os.SEEK_END)
        offset = self.pages.tell()
        self.pages.write(content)
        return offset

class Crawler:
    def __init__(self):
        self.indexdb = None
        self.datafile = None
        self.headers = {}
        self.downloader = Downloader(self)
        self.pager = Pager(self)

    def open(self):
        self.indexdb.open()
        self.pager.open()

    def close(self):
        self.indexdb.finish()
        self.indexdb.close()
        self.pager.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, extype, exvalue, extrace):
        self.close()

    def addlink(self, url, weight):
        pagelink = pagedb.WaitingUrl.get_byurl(self.indexdb, url)
        if pagelink == None:
            pagelink = pagedb.WaitingUrl.create(self.indexdb, 0, 1, weight, url)
        else:
            if pagelink.weight < weight:
                pagelink.weight = weight
            pagelink.seqno = 0
            pagelink.refcount += 1
            pagelink.update(self.indexdb)

    def download(self):
        return self.downloader.download()

    @classmethod
    def load(cls, filename):
        with open(filename) as fcrawler:
            ycrawler = yaml.load(fcrawler, Loader=yaml.Loader)
            crawler = cls()
            crawler.indexdb = Db(ycrawler['index'], pagedb.structure)
            crawler.datafile = ycrawler['data']
            for jheader in ycrawler['request']['headers']:
                crawler.headers[jheader['name'].lower()] = jheader['value']
            return crawler

def load(fcrawler):
    return Crawler.load(fcrawler)



