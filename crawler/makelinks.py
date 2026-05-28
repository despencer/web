#!/usr/bin/python3

import argparse
import crawler

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Adds links for one page for crawling')
    parser.add_argument('crawler', help='Crawler file')
    parser.add_argument('pageid', help='Page ID', type=int)
    args = parser.parse_args()
    with crawler.load(args.crawler) as crawl:
        for l in crawl.extract_links(crawl.getpage(args.pageid), True):
            print(f'{l.seqno}, {l.refcount}, {l.weight}, {l.url}')