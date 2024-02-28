class HttpRequest:
    def __init__(self):
        self.method = 'GET'
        self.url = ''
        self.headers = {}
        self.cookies = []

class Browser:
    def __init__(self, gateway):
        self.gateway = gateway

    def loadpage(self, url):
        req = HttpRequest()
        req.url = url
        self.gateway.request(req)
