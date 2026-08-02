#!/usr/bin/python3

import argparse
import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')
sys.path.append(os.path.dirname(__file__) + '/../text')
from bs4 import BeautifulSoup
import har
import mdmaker
import files

def get_storage(filename):
    ext = os.path.splitext(filename)[1]
    if ext == '.har':
        return har.load(filename)
    if ext == '.html':
        return files.load(filename)
    print(f'Unknown extension {ext}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract html code')
    parser.add_argument('response', help='Source HAR-file or html file with response')
    parser.add_argument('mdmaker', help='Markdown maker definition')
    parser.add_argument('md', help='Target md-file')
    args = parser.parse_args()
    container = get_storage(args.response)
    resp = container.response
    if resp.content_type() == 'text/html':
        document = BeautifulSoup(resp.content, 'html.parser')
        with open(args.md, 'w', encoding='utf-8') as mdfile:
            mdmaker.load(args.mdmaker).make(document, container, os.path.splitext(args.md)[0], mdfile)
    else:
        print('HTML not found')
