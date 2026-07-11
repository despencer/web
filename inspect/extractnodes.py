#!/usr/bin/python3

import argparse
from bs4 import BeautifulSoup

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract nodes from HTML')
    parser.add_argument('html', help='Source html-file')
    parser.add_argument('selector', help='Selector for finding nodes')
    args = parser.parse_args()
    with open(args.html) as hfile:
        document = BeautifulSoup(hfile, 'html.parser')
        for node in document.find_all(**eval(args.selector)):
            print(node)