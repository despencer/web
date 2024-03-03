from datetime import datetime, timedelta, timezone
import json
import xml.dom
import urllib
import webhttp
import webhtml
import webscript

def loadhttpheaders(jheaders):
    headers = {}
    for jheader in jheaders:
        headers[jheader['name']] = jheader['value']
    return headers

def savehttpheaders(headers):
    jheaders = []
    for name, value in headers.items():
        jheaders.append( { 'name':name, 'value':value } )
    return jheaders

def loadhttpcookies(jcookies):
    cookies = []
    for jc in jcookies:
        ck = HttpCookie()
        ck.name = jc['name']
        ck.value = jc['value']
        ck.path = jc['path']
        ck.domain = jc['domain']
        if 'expires' in jc:
            ck.expires = datetime.fromisoformat(jc['expires'])
        cookies.append(ck)
    return cookies

def savehttpcookies(cookies):
    jcookies = []
    for c in cookies:
        jc = { 'name':c.name, 'value':c.value, 'domain':c.domain, 'path':c.path }
        if c.expires != None:
            jc['expires'] = c.expires.isoformat()
        jcookies.append( jc )
    return jcookies

def loadhttpquery(jquery):
    query = {}
    for jq in jquery:
        query[jq['name']] = jq['value']
    return query

def savehttpquery(query):
    jquery = []
    for n,v in query.items():
        jquery.append( { 'name':n, 'value':v } )
    return jquery

def loadhttprequest(jreq):
    req = HttpRequest()
    req.method = jreq['method']
    req.url = jreq['url']
    req.headers = loadhttpheaders(jreq['headers'])
    if 'queryString' in jreq:
        req.query = loadhttpquery(jreq['queryString'])
    if 'cookies' in jreq:
        req.cookies = loadhttpcookies(jreq['cookies'])
    return req

def savehttprequest(req):
    return { 'method':req.method, 'url':req.url, 'headers':savehttpheaders(req.headers), 'queryString':savehttpquery(req.query), 'cookies':savehttpcookies(req.cookies) }

def loadhttpresponse(jresp):
    resp = webhttp.HttpResponse()
    resp.status = jresp['status']
    resp.content = jresp['content']['text']
    resp.headers = loadhttpheaders(jresp['headers'])
#    resp.cookies = loadhttpcookies(jresp['cookies'])
    return resp

def savehttpresponce(resp):
    return { 'status':resp.status, 'text':resp.text, 'headers':savehttpheaders(resp.headers), 'cookies':savehttpcookies(resp.cookies) }

def saveresponce(harfile, request, responce):
    jentry = { 'request' : savehttprequest(request), 'response' : savehttpresponce(responce) }
    with open(harfile, 'w') as jfile:
        json.dump( { 'log':{ 'entries' : [ jentry ] } } , jfile, indent = 4 )

def loadresponce(harfile):
    with open(harfile) as hfile:
        jfile = json.load(hfile)
        jresp = jfile['log']['entries'][0]['response']
        return loadhttpresponce(jresp)

def loadrequest(harfile):
    with open(harfile) as hfile:
        jfile = json.load(hfile)
        jreq = jfile['log']['entries'][0]['request']
        return loadhttprequest(jreq)

class Imitator:
    def __init__(self, jhar, output):
        self.jhar = jhar
        self.output = output
        self.processed = []

    def request(self, req):
        response = None
        for jentry in self.jhar['log']['entries']:
            if jentry['request']['url'] == req.url:
                self.processed.append(req.url)
                response = loadhttpresponse(jentry['response'])
                break
        if response == None:
            self.output.write('Url "{0}" is not found\n'.format(req.url))
            response = webhttp.HttpResponse()
            response.status = webhttp.HttpResponse.RESPONSE_NOTFOUND
        response.request = req
        return response

    def check(self):
        for jentry in self.jhar['log']['entries']:
            url = jentry['request']['url']
            if url not in self.processed:
                self.output.write('Url "{0}" has not been requested\n'.format(url))

def getscripts(doc, jhar, baseurl):
    scripts = []
    for node in webhtml.traverse(doc):
        if node.nodeType == xml.dom.Node.ELEMENT_NODE and node.nodeName == "script":
            path = webhtml.getnodepath(node)
            if 'src' in node.attributes:
                url = urllib.parse.urljoin(baseurl, node.attributes['src'].value)
                script = None
                for jentry in jhar:
                   if jentry['request']['url'] == url:
                        script = webscript.HtmlScript(path, jentry['response']['content']['text'], url=url)
                        break
                if script == None:
                    print('url {0} not found'.format(url))
                else:
                    scripts.append(script)
            else:
                source = ''
                for cn in node.childNodes:
                    source += cn.data
                scripts.append( webscript.HtmlScript(path, source) )
    return scripts