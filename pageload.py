#!/usr/bin/python3

import argparse
import requests
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup

ua = 'User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0'

# url = 'https://rebrickable.com/downloads'
# url = 'https://maps.yandex.ru'
# headers = { 'user-agent' : 'User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0' }
# resp = requests.get(url, headers=headers)
# print(resp.history)
# soup = BeautifulSoup(resp.text)
# file = open("yandex.html","w")
# file.write(soup.prettify())
# file.close()

def dumpdict(fname, adict):
    with open(fname, 'w') as fh:
        for n,v in adict.items():
            fh.write("{0}: {1}\n".format(n, v))


def download(name, url):
    headers = { 'user-agent' : ua }
    resp = requests.get(url, headers=headers, allow_redirects=False)
    print("Response", resp.status_code)
    soup = BeautifulSoup(resp.text, 'html.parser')
    with open(name+'.html', 'w') as hf:
        hf.write(soup.prettify())
    dumpdict(name+'.headers', resp.headers)
    dumpdict(name+'.cookies', resp.cookies)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Load http page')
    parser.add_argument('name', help='specifies name and files')
    parser.add_argument('url', help='specifies url')
    args = parser.parse_args()
    url = urlparse(args.url)
    if url.scheme == '':
        url = url._replace(scheme = 'https')
    if url.netloc == '':
        url = url._replace(netloc = url.path, path = '')
    url = urlunparse(url)
    print('Download', url, 'into', args.name)
    download(args.name, url)
