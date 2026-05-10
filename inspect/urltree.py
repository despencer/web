#!/usr/bin/python3

import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')
import har
import webhttp

def get_page_index(session, url):
    for idx, e in enumerate(session.entries):
        if url == e.request.url:
            return idx

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Making URL tree')
    parser.add_argument('session', help='Source HAR-file with session')
    args = parser.parse_args()
    session = har.load(args.session)
    for e in session.entries:
        print(e.request.url)
        if e.response.status == webhttp.RESPONSE_REDIRECT:
            print('    Redirect to', e.response.headers['location'])
        if 'referer' in e.request.headers:
            print(f'    From ({get_page_index(session,e.request.headers['referer'])})',e.request.headers['referer'])
