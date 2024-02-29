from datetime import datetime, timedelta, timezone

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
            ck.expires = datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(seconds=c.expires) if c.expires != None else None
            self.cookies.append(ck)

class Browser:
    def __init__(self, gateway):
        self.gateway = gateway

    def loadpage(self, url):
        req = HttpRequest()
        req.url = url
        self.gateway.request(req)
