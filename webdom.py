import xml.dom
from urllib.parse import urlparse
import webhtml
import webdombase
import webdomxml
import webdombs

class Navigator:
    def __init__(self, userAgent):
        self.userAgent = userAgent

class Console:
    def log(self, *msg):
        print(*msg)

class Event:
    def __init__(self, args):
        self.func = args[0]
        if len(args) >= 2:
            self.delay = args[1]
        self.args = args[2:]

    def execute(self, jscontext):
        if len(self.args) > 0:
            raise Exception ('Timeout with arguments not yet implemented')
        jscontext.calljsfunc(self.func)

class Location:
    def __init__(self, url):
        u = urlparse(url)
        self.href = url
        self.hostname = u.hostname

class Window(webdombase.EventTarget):
    def __init__(self):
        self.window = self
        self.events = []
        self.console = Console()

    def processevents(self, jscontext):
        while len(self.events) > 0:
            self.events.pop(0).execute(jscontext)

    def setTimeout(self, *args):
        self.events.append( Event(args) )

def parsedom(content, builder = 'html5lib'):
    return { 'html5lib': webdomxml.parse, 'bs4': webdombs.parse }[builder](content)

def setupcontext(dom, httpcontext, baseurl):
    window = Window()
    window.document = dom
    window.navigator = Navigator(httpcontext.useragent)
    window.location = Location(baseurl)
    return window
