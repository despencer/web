from datetime import datetime, timedelta, timezone
import json

class HttpCookie:
    def __init__(self):
        self.name = ''
        self.value = ''
        self.domain = ''
        self.path = '/'
        self.expires = None

class HttpRequest:
    def __init__(self):
        self.method = 'GET'
        self.url = ''
        self.headers = {}

class HttpResponce:
    def __init__(self):
        self.status = 0
        self.text = ''
        self.headers = {}
        self.cookies = []

    def setheaders(self, headers):
        for n,v in headers.items():
           self.headers[n]=v

    def setcookies(self, cjar):
        for c in cjar:
            ck = HttpCookie()
            ck.name = c.name
            ck.value = c.value
            ck.path = c.path
            ck.domain = c.domain
            ck.expires = datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(seconds=c.expires)
            self.cookies.append(ck)

def loadrequest(harfile):
    with open(harfile) as hfile:
        jfile = json.load(hfile)
        jreq = jfile['log']['entries'][0]['request']
        req = HttpRequest()
        req.method = jreq['method']
        req.url = jreq['url']
        for jheader in jreq['headers']:
            req.headers[jheader['name']] = jheader['value']
    return req

def savehttpheaders(headers):
    jheaders = []
    for name, value in headers.items():
        jheaders.append( { 'name':name, 'value':value } )
    return jheaders

def savehttpcookies(cookies):
    jcookies = []
    for c in cookies:
        jcookies.append( { 'name':c.name, 'value':c.value, 'domain':c.domain, 'path':c.path, 'expires':c.expires.isoformat() } )
    return jcookies

def savehttprequest(req):
    return { 'method':req.method, 'url':req.url, 'headers':savehttpheaders(req.headers) }

def savehttpresponce(resp):
    return { 'status':resp.status, 'text':resp.text, 'headers':savehttpheaders(resp.headers), 'cookies':savehttpcookies(resp.cookies) }

def saveresponce(harfile, request, responce):
    jentry = { 'request' : savehttprequest(request), 'responce' : savehttpresponce(responce) }
    with open(harfile, 'w') as jfile:
        json.dump( { 'log':{ 'entries' : [ jentry ] } } , jfile, indent = 4 )

