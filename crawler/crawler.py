import logging
import yaml
import sys
import os
sys.path.append(os.path.expanduser('~/dev/pydma'))
from dbmeta import Db
import pagedb

class Crawler:
    def __init__(self):
        self.indexdb = None

    def open(self):
        self.indexdb.open()

    def close(self):
        self.indexdb.finish()
        self.indexdb.close()

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

    @classmethod
    def load(cls, filename):
        with open(filename) as fcrawler:
            ycrawler = yaml.load(fcrawler, Loader=yaml.Loader)
            crawler = cls()
            crawler.indexdb = Db(ycrawler['index'], pagedb.structure)
            return crawler

def load(fcrawler):
    return Crawler.load(fcrawler)



