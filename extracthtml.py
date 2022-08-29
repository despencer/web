#!/usr/bin/python3

import argparse
import har
import html5lib
from xml.etree import ElementTree

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract html code')
    parser.add_argument('responce', help='Source HAR-file with responce')
    parser.add_argument('html', help='Target html-file')
    args = parser.parse_args()
    resp = har.loadresponce(args.responce)
    processed = False
    if 'Content-Type' in resp.headers:
        if resp.headers['Content-Type'].split(';')[0] == 'text/html':
            document = html5lib.parse(resp.text)
            ElementTree.indent(document)
            with open(args.html, 'w') as hfile:
                hfile.write(ElementTree.tostring(document, encoding='unicode'))
            processed = True
    if not processed:
        with open(args.html, 'w') as hfile:
            hfile.write(resp.text)
