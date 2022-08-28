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
    document = html5lib.parse(resp.text)
    ElementTree.indent(document)
    with open(args.html, 'w') as hfile:
        hfile.write(ElementTree.tostring(document, encoding='unicode'))
