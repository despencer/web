#!/usr/bin/env python

import argparse
import logging
import crawler

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Runs the crawling')
    parser.add_argument('crawler', help='Crawler file')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG, filename=args.crawler+'.log', filemode='w', format='%(asctime)s %(name)s %(levelname)s %(message)s')
    with crawler.load(args.crawler) as crawl:
        print('Press ENTER to stop')
        crawl.run()
        input()
        crawl.stop()
