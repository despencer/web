#!/usr/bin/python3

import argparse
import requests
import har
import webhttp

def save(harfile, request, responce):
    resp = webhttp.HttpResponse()
    resp.status = responce.status_code
    resp.content = responce.text
    resp.setheaders(responce.headers)
    resp.setcookies(responce.cookies)
    har.saveresponse(harfile, request, resp)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make http request')
    parser.add_argument('request', help='HAR-file with request')
    parser.add_argument('response', help='Target HAR-file with response')
    args = parser.parse_args()
    req = har.loadrequest(args.request)
    response = requests.request(req.method, req.url, headers=req.headers, params=req.query, allow_redirects=False)
    save(args.response, req, response)
