import html5lib
import xml.dom
import webdombase

class NodeProxy(webdombase.EventTarget):
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
        if self.node.__class__.__name__ == 'DocumentFragment':
            return self.manager.get(self.node.ownerDocument.createElement(tagname))
        return self.manager.get(self.node.createElement(tagname))

    def createDocumentFragment(self):
        return self.manager.get(self.node.createDocumentFragment())

    def createHTMLDocument(self, title):
        return self.manager.get(webhtml.parse('<html><head><title>' + title + '</title></head><body></body></html>'))

    def getElementsByTagName(self, tagname):
        return self.manager.get(self.node.getElementsByTagName(tagname) )

    def querySelector(self, selectors):
        return self.manager.get(self.node.querySelector(selectors) )

    def setAttribute(self, name, value):
        self.node.setAttribute(name, value)

    def cloneNode(self, deep):
        return self.manager.get(self.node.cloneNode(deep))

    def createEvent(self, jstype):
        return DomEvent(jstype)


def parse(content):
    pm = webdombase.ProxyManager(NodeProxy,
                   ['Node', 'DocumentFragment', 'Attr', 'Element', 'CharacterData',
                   'Text', 'CDATASection', 'DocumentType', 'Entity', 'Notation', 'ElementInfo', 'Document',
                   'DOMImplementation'],
                   [ 'EmptyNodeList', 'NodeList' ],
                   ['str','int'] )
    return pm.get(html5lib.parse(content, treebuilder='dom'))
