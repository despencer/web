import logging
import yaml
import sys
import os
import urllib.parse
from datetime import datetime, timezone
import html5lib
import threading
import time
sys.path.append(os.path.expanduser('~/dev/pydma'))
from dbmeta import Db, DbMeta
import pagedb
sys.path.append(os.path.dirname(__file__) + '/..')
import webhtml
import matcher
import downloader

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

    def savepage(self, page, filename):
        with open(filename, 'wb') as f:
            f.write(self.load(page))

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
            l.url = urllib.parse.unquote(urllib.parse.urldefrag(l.url).url)
            result[l.url] = l
        return result

    def prepare(self, links, store):
        result = []
        for l in links:
            if len(pagedb.Page.get_byurl(self.crawler.indexdb, l.url)) > 0:
                continue
            wu = pagedb.WaitingUrl.get_byurl(self.crawler.indexdb, l.url)
            if wu == None:
                weight = self.crawler.matcher.get_weight(l)
                if weight > 0:
                    wu = pagedb.WaitingUrl.create(self.crawler.indexdb, self.crawler.indexdb.genid(), 1, weight, l.url)
                    if store:
                        wu.insert(self.crawler.indexdb)
                        logging.info(f'Url {wu.url} added')
                    result.append(wu)
            else:
                wu.refcount += 1
                if store:
                    wu.update(self.crawler.indexdb)
                result.append(wu)
        return result

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
    def __init__(self, policy):
        self.indexdb = None
        self.datafile = None
        self.headers = {}
        self.downloader = downloader.Downloader(self, policy)
        self.pager = Pager(self)
        self.extractor = Extractor(self)
        self.matcher = matcher.Matcher()

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
        self.indexdb.finish()
        return pagelink

    def download(self):
        return self.downloader.download()

    def extract_links(self, page, store):
        return self.extractor.extract(page, store)

    def extract_page(self, url, filename):
        pages = pagedb.Page.get_byurl(self.indexdb, url)
        if len(pages) == 0:
            return False
        self.pager.savepage(pages[0], filename)
        return True

    @classmethod
    def load(cls, filename, policy=downloader.Policy.single()):
        with open(filename) as fcrawler:
            ycrawler = yaml.load(fcrawler, Loader=yaml.Loader)
            crawler = cls(policy)
            crawler.indexdb = Db(ycrawler['index'], pagedb.structure)
            crawler.datafile = ycrawler['data']
            crawler.downloader.load(ycrawler)
            for jheader in ycrawler['request']['headers']:
                crawler.headers[jheader['name'].lower()] = jheader['value']
            crawler.matcher.load(ycrawler['links'])
            return crawler


class Runner:
    def __init__(self):
        self.thread = None
        self.keeprunning = False

    def run(self, fcrawler):
        self.thread = threading.Thread(target = self.loop, args=(fcrawler, ), daemon=True)
        self.thread.start()
        input()
        self.stop()

    def loop(self, fcrawler):
        with Crawler.load(fcrawler, policy=downloader.Policy.default()) as crawl:
            print('Press ENTER to stop')
            self.keeprunning = True
            while self.keeprunning:
                result = crawl.download()
                if result == None:
                    print('Nothing left to download')
                    self.stop()
                else:
                    if result.page != None:
                        crawl.extract_links(result.page, True)

    def stop(self):
        self.keeprunning = False

def load(fcrawler):
    return Crawler.load(fcrawler)

def run(fcrawler):
    Runner().run(fcrawler)
