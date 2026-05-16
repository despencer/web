#!/usr/bin/python3

import argparse
import crawler

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Downloads one page for crawling')
    parser.add_argument('crawler', help='Crawler file')
    args = parser.parse_args()
    with crawler.load(args.crawler) as crawl:
        page = crawl.download()
        print(f'Load {page.url} as #{page.id}')
