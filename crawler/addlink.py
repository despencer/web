#!/usr/bin/python3
import logging
import argparse
import crawler

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Adds a page for crawling')
    parser.add_argument('crawler', help='Crawler file')
    parser.add_argument('page', help='URL to add')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG, filename=args.crawler+'.log', filemode='w', format='%(asctime)s %(name)s %(levelname)s %(message)s')
    with crawler.load(args.crawler) as crawl:
        pagelink = crawl.addlink(args.page, 1000)
        print(f'Pagelink {pagelink.id} weight {pagelink.weight} refcount {pagelink.refcount}')
