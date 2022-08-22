import json

class HttpRequest:
    def __init__(self):
        self.method = 'GET'
        self.url = ''
        self.headers = {}

def loadrequest(harfile):
    with open(harfile) as hfile:
        jfile = json.load(hfile)
        jreq = jfile['log']['entries'][0]['request']
        req = HttpRequest()
        req.method = jreq['method']
        req.url = jreq['url']
        for jheader in jreq['headers']:
            req.headers[jheader['name']] = [jheader['value']]
    return req
