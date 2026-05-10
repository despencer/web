#!/usr/bin/python3

import argparse
import crawler

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Adds a page for crawling')
    parser.add_argument('crawler', help='Crawler file')
    parser.add_argument('page', help='URL to add')
    args = parser.parse_args()
    with crawler.load(args.crawler) as crawl:
        pass
#        crawl.addlink(args.url, 1000)