#!/usr/bin/python3

import argparse
import sys
import os
sys.path.insert(1, os.path.abspath('../pydma'))

from dbmeta import DbPackaging

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make initial loading task')
    parser.add_argument('project', help='specifies db name')
    parser.add_argument('url', help='specifies url')
    args = parser.parse_args()
    db = DbPackaging()
    db.open(args.project)
    db.close()
