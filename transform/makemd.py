#!/usr/bin/python3

import argparse
import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')
sys.path.append(os.path.dirname(__file__) + '/../text')
import har
import mdmaker
from bs4 import BeautifulSoup

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract html code')
    parser.add_argument('response', help='Source HAR-file with response')
    parser.add_argument('mdmaker', help='Markdown maker definition')
    parser.add_argument('md', help='Target md-file')
    args = parser.parse_args()
    resp = har.loadresponse(args.response)
    processed = False
    if 'content-type' in resp.headers:
        if resp.headers['content-type'].split(';')[0] == 'text/html':
            document = BeautifulSoup(resp.content, 'html.parser')
            with open(args.md, 'w', encoding='utf-8') as mdfile:
                mdmaker.load(args.mdmaker).make(document, resp, mdfile)
            processed = True
    if not processed:
        print('HTML not found')
