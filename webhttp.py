from datetime import datetime, timedelta, timezone
import webhtml

class HttpRequest:
    def __init__(self):
        self.method = 'GET'
        self.url = ''
        self.headers = {}
        self.cookies = []

class HttpCookie:
    def __init__(self):
        self.name = ''
        self.value = ''
        self.domain = ''
        self.path = '/'
        self.expires = None

class HttpResponse:
    RESPONSE_OK = 200
    RESPONSE_MOVED = 301
    RESPONSE_REDIRECT = 302
    RESPONSE_NOTFOUND = 404

    def __init__(self):
        self.request = None
        self.status = 0
        self.content = ''
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
            ck.expires = datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(seconds=c.expires) if c.expires != None else None
            self.cookies.append(ck)

class Cache:
    def __init__(self):
        self.pages = {}

    def append(self, response):
        self.pages[response.request.url] = response

    def get(self, url):
        if url in self.pages:
            return self.pages[url]
        return None

    def clear(self):
        self.pages.clear()

class Browser:
    def __init__(self, gateway):
        self.gateway = gateway
        self.cache = Cache()

    def makerequest(self, url):
        req = HttpRequest()
        req.url = url
        resp = self.gateway.request(req)
        self.cache.append(resp)
        while resp.status in (HttpResponse.RESPONSE_MOVED, HttpResponse.RESPONSE_REDIRECT):
            req = HttpRequest()
            req.url = resp.headers['location']
            resp = self.gateway.request(req)
            self.cache.append(resp)
        return resp

    def loadpage(self, url):
        self.cache.clear()
        resp = self.makerequest(url)
        if resp.status == HttpResponse.RESPONSE_OK:
            dom = webhtml.parse(resp.content)
            for l in webhtml.getlinks(dom, url):
                if l.usage in ('script', 'image', 'css'):
                    self.makerequest(l.url)
