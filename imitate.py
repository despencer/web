#!/usr/bin/python3

import argparse
import json
import webhttp
import har

def main(args):
    with open(args.har) as hfile:
        jfile = json.load(hfile)
        imitator = har.Imitator(jfile)
        browser = webhttp.Browser(imitator)
        browser.loadpage(jfile['log']['entries'][0]['request']['url'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Imitates a browser via har file')
    parser.add_argument('har', help='a har file')
    args = parser.parse_args()
    main(args)
