#!/usr/bin/python3

import argparse
import har

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract html code')
    parser.add_argument('responce', help='Source HAR-file with responce')
    parser.add_argument('html', help='Target html-file')
    args = parser.parse_args()
    resp = har.loadresponce(args.responce)
    with open(args.html, 'w') as hfile:
        hfile.write(resp.text)