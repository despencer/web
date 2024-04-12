import xml.dom
import urllib
import webhtml
import webhttp

class HtmlScript:
    def __init__(self, path, source, url=None):
        self.path = path
        self.source = source
        self.url = url

class NodeProxy:
    def __init__(self, node):
        self.node = node

class JavaScriptEngine:
    def __init__(self, context, browser, dom, baseurl):
        self.context = context
        self.browser = browser
        self.dom = dom
        self.baseurl = baseurl

    def run(self):
        self.init()
        scripts = self.getscripts()
        while len(scripts) > 0:
            node = scripts.pop(0)
            code = self.getcode(node)
            self.execute(code)

    def init(self):
        self.context.add( {'document':NodeProxy(self.dom)} )

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
        self.context.execute(code)
