#!/usr/bin/python3

import argparse
import requests
import har

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make http request')
    parser.add_argument('request', help='HAR-file with request')
    parser.add_argument('responce', help='Target HAR-file with responce')
    args = parser.parse_args()
    req = har.loadrequest(args.request)
