#!/usr/bin/python3

import argparse
import crawler

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extracts crawled page')
    parser.add_argument('crawler', help='Crawler file')
    parser.add_argument('url', help='URL to retrieve')
    parser.add_argument('filename', help='Filename to store')
    args = parser.parse_args()
    with crawler.load(args.crawler) as crawl:
        if not crawl.extract_page(args.url, args.filename):
            print('Page does not exist')
