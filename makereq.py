#!/usr/bin/python3

import argparse
import requests
import har

def save(harfile, request, responce):
    resp = har.HttpResponce()
    resp.status = responce.status_code
    resp.text = responce.text
    resp.setheaders(responce.headers)
    resp.setcookies(responce.cookies)
    har.saveresponce(harfile, request, resp)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make http request')
    parser.add_argument('request', help='HAR-file with request')
    parser.add_argument('responce', help='Target HAR-file with responce')
    args = parser.parse_args()
    req = har.loadrequest(args.request)
    responce = requests.request(req.method, req.url, headers=req.headers, allow_redirects=False)
    save(args.responce, req, responce)
