#!/usr/bin/python3

import argparse
import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')
import har
import html5lib
from xml.etree import ElementTree

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract html code')
    parser.add_argument('response', help='Source HAR-file with response')
    parser.add_argument('html', help='Target html-file')
    args = parser.parse_args()
    resp = har.loadresponse(args.response)
    processed = False
    if 'content-type' in resp.headers:
        if resp.headers['content-type'].split(';')[0] == 'text/html':
            document = html5lib.parse(resp.content)
            ElementTree.indent(document)
            with open(args.html, 'w') as hfile:
                hfile.write(ElementTree.tostring(document, encoding='unicode'))
            processed = True
    if not processed:
        with open(args.html, 'w') as hfile:
            hfile.write(resp.content)
