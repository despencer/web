#!/usr/bin/python3

import argparse
import sys
import os
sys.path.insert(1, os.path.abspath('../pydma'))
import webdb
from dbmeta import Db

def run_loading(db, id):
    task = webdb.UrlTask.get(db, id)
    print('run', task.id, task.url)

def runtask(db, task):
    handlers = { 'url':run_loading }
    if task.status == 'init':
        handlers[task.kind](db, task.id)
    else:
        print('Non-ready task', task.id, task.status, '(', task.kind, ')')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run task')
    parser.add_argument('project', help='specifies db name')
    parser.add_argument('task', help='specifies task')
    args = parser.parse_args()
    with Db(args.project) as db:
        webdb.check(db)
        with db.run() as run:
            runtask(run, webdb.Task.get(run, args.task))
