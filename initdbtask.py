#!/usr/bin/python3

import argparse
import sys
import os
sys.path.insert(1, os.path.abspath('../pydma'))
import webdb
from dbmeta import Db

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make initial loading task')
    parser.add_argument('project', help='specifies db name')
    parser.add_argument('url', help='specifies url')
    args = parser.parse_args()
    with Db(args.project) as db:
        webdb.check(db)
        with db.run() as run:
            id = webdb.UrlTask.create(run, args.url).id
            print('Task', id, 'created')