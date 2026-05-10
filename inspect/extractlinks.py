#!/usr/bin/python3

import argparse
import sys
import os
import html5lib
sys.path.append(os.path.dirname(__file__) + '/..')
import webhtml

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract links from HTML')
    parser.add_argument('html', help='Source html-file')
    parser.add_argument('base', help='Base URL')
    args = parser.parse_args()
    with open(args.html) as hfile:
        document = html5lib.parse(hfile.read(), treebuilder='dom')
        for l in webhtml.getlinks(document, args.base):
            print(l.url)
