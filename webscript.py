import xml.dom
import urllib
import webhtml
import webhttp
import webdom

class HtmlScript:
    def __init__(self, path, source, url=None):
        self.path = path
        self.source = source
        self.url = url

class JavaScriptEngine:
    def __init__(self, context, browser, window, dom, baseurl):
        self.context = context
        self.browser = browser
        self.window = window
        self.dom = dom
        self.baseurl = baseurl

    def run(self):
        scripts = self.getscripts()
        while len(scripts) > 0:
            node = scripts.pop(0)
            code = self.getcode(node)
            self.execute(code)
        self.window.processevents(context)

    def getscripts(self):
        scripts = []
        for node in webhtml.traverse(self.dom):
            if node.nodeType == xml.dom.Node.ELEMENT_NODE and node.nodeName == "script":
                scripts.append(node)
        return scripts

    def getcode(self, node):
        code = ''
        if 'src' in node.attributes:
            urlsrc = urllib.parse.urljoin(self.baseurl, node.attributes['src'].value)
            resp = self.browser.makerequest(urlsrc)
            if resp.status == webhttp.HttpResponse.RESPONSE_OK:
                code = resp.content
            else:
                print('Script {0} not found'.format(urlsrc))
        else:
            for cn in node.childNodes:
                code += cn.data
        return code

    def execute(self, code):
        try:
            self.context.execute(code)
        except Exception as e:
            print(e)
            print('/* ------- script -------- */')
            print(code)
            print('/* ======================= */')
