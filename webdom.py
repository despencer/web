import xml.dom
import webhtml

class ContainerProxy:
    def __init__(self, manager, collection):
        self.manager = manager
        self.collection = collection

class NodeProxy:
    def __init__(self, manager, node):
        self.manager = manager
        self.node = node
        self.checkattrs( ['nodeType', 'documentElement', 'lastChild', 'childNodes', 'implementation'] )
        if hasattr(self, 'nodeType') and self.nodeType == xml.dom.Node.DOCUMENT_NODE:
            self.body = self.selectfirst('body')
            self.title = self.selectfirst(['head','title'])
            if self.title != None:
                self.title = self.title.gettext()

    def checkattrs(self, names):
        for name in names:
            if hasattr(self.node, name):
                setattr(self, name, self.manager.get(getattr(self.node, name)))

    def selectfirst(self, selector):
        if isinstance(selector, list):
            head = self.selectfirst(selector[0])
            if head == None:
                return None
            if len(selector) > 1:
                return head.selectfirst( selector[1:] )
            return head
        nodes = self.node.getElementsByTagName(selector)
        if len(nodes) > 0:
            return self.manager.get(nodes[0])
        return None

    def gettext(self):
        return "".join(t.nodeValue for t in self.node.childNodes if t.nodeType == t.TEXT_NODE)

    def appendChild(self, node):
        node = self.manager.restore(node)
        return self.manager.get(self.node.appendChild(node))

    def createElement(self, tagname):
        return self.manager.get(self.node.createElement(tagname))

    def createDocumentFragment(self):
        return self.manager.get(self.node.createDocumentFragment())

    def createHTMLDocument(self, title):
        return self.manager.get(webhtml.parse('<html><head><title>' + title + '</title></head><body></body></html>'))

    def setAttribute(self, name, value):
        self.node.setAttribute(name, value)

    def cloneNode(self, deep):
        return self.manager.get(self.node.cloneNode(deep))

    def createEvent(self, jstype):
        return DomEvent(jstype)

    def addEventListener(self, evtype, listener, *opt):
        pass

class ProxyManager:
    def __init__(self):
        self.proxies = {}
        self.back = {}
        self.proxyconts = [ 'EmptyNodeList', 'NodeList' ]
        self.proxyclasses = ['Node', 'DocumentFragment', 'Attr', 'Element', 'CharacterData',
                   'Text', 'CDATASection', 'DocumentType', 'Entity', 'Notation', 'ElementInfo', 'Document',
                   'DOMImplementation']
        self.passclasses = ['str','int']

    def get(self, obj):
        if obj == None:
            return None
        if obj.__class__.__name__ in self.proxyconts:
            return ContainerProxy(self, obj)
        if obj in self.proxies:
            return self.proxies[obj]
        if obj.__class__.__name__ in self.passclasses:
            return obj
        if obj.__class__.__name__ in self.proxyclasses:
            self.proxies[obj] = NodeProxy(self, obj)
            self.back[ self.proxies[obj] ] = obj
            return self.proxies[obj]
        raise Exception( 'Unknown class ' + obj.__class__.__name__ + ' for ProxyManager')

    def restore(self, obj):
        if obj in self.back:
            return self.back[obj]
        return obj

class DomEvent:
    def __init__(self, jstype):
        self.jstype = jstype

    def initCustomEvent(self, name, canBubble, cancelable, detail):
        pass

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

class Window:
    def __init__(self):
        self.window = self
        self.events = []
        self.console = Console()

    def processevents(self, jscontext):
        while len(self.events) > 0:
            self.events.pop(0).execute(jscontext)

    def setTimeout(self, *args):
        self.events.append( Event(args) )

def setupcontext(dom):
    window = Window()
    pm = ProxyManager()
    window.document = pm.get(dom)
    return window
