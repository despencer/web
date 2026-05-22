import logging
import yaml
import sys
import os
import random
import urllib.parse
from datetime import datetime, timezone
import requests
import html5lib
sys.path.append(os.path.expanduser('~/dev/pydma'))
from dbmeta import Db, DbMeta
import pagedb
sys.path.append(os.path.dirname(__file__) + '/..')
import webhtml

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
        page.insert(self.crawler.indexdb)
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

    def load(self, page):
        self.pages.seek(page.offset)
        return self.pages.read(page.length)

class Extractor:
    def __init__(self, crawler):
        self.crawler = crawler

    def extract(self, page, store):
        links = self.get_rawlinks(page)
        links = self.clean(links)
        links = self.prepare(links.values(), store)
        if store:
            self.crawler.indexdb.finish()
        return links

    def get_rawlinks(self, page):
        if page.status_code != 200 or page.pagetype.split(';')[0] != 'text/html':
            return []
        content = self.crawler.pager.load(page).decode(self.get_charset(page))
        document = html5lib.parse(content, treebuilder='dom')
        return webhtml.getlinks(document, page.url)

    def clean(self, links):
        result = {}
        for l in links:
            l.url = urllib.parse.urldefrag(l.url).url
            result[l.url] = l
        return result

    def prepare(self, links, store):
        result = []
        for l in links:
            wu = pagedb.WaitingUrl.get_byurl(self.crawler.indexdb, l.url)
            if wu == None:
                weight = self.get_weight(l)
                if weight > 0:
                    wu = pagedb.WaitingUrl.create(self.crawler.indexdb, self.crawler.indexdb.genid(), 1, weight, l.url)
                    if store:
                        wu.insert(self.crawler.indexdb)
                    result.append(wu)
            else:
                wu.refcount += 1
                if store:
                    wu.update(self.crawler.indexdb)
                result.append(wu)
        return result

    def get_weight(self, link):
        return 1

    def get_charset(self, page):
        if ';' not in page.pagetype or 'charset' not in page.pagetype:
            print(f'No charset ({page.pagetype}) in page #{page.id} {page.url}')
            return 'utf-8'
        charset = page.pagetype.split(';')[1]
        if 'charset' not in page.pagetype:
            print(f"Can't decode charset from '{page.pagetype}' in page #{page.id} {page.url}")
            return 'utf-8'
        return charset.split('=')[1].strip()

class Crawler:
    def __init__(self):
        self.indexdb = None
        self.datafile = None
        self.headers = {}
        self.downloader = Downloader(self)
        self.pager = Pager(self)
        self.extractor = Extractor(self)

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

    def getpage(self, pageid):
        return pagedb.Page.get(self.indexdb, pageid)

    def addlink(self, url, weight):
        pagelink = pagedb.WaitingUrl.get_byurl(self.indexdb, url)
        if pagelink == None:
            pagelink = pagedb.WaitingUrl.create(self.indexdb, 0, 1, weight, url)
            pagelink.insert(self.indexdb)
        else:
            if pagelink.weight < weight:
                pagelink.weight = weight
            pagelink.seqno = 0
            pagelink.refcount += 1
            pagelink.update(self.indexdb)

    def download(self):
        return self.downloader.download()

    def extract_links(self, page, store):
        return self.extractor.extract(page, store)

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



