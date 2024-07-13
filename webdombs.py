import bs4
import xml.dom
import webdombase

class Node(webdombase.Proxy):
    def __init__(self, manager, node, nodeType):
        webdombase.Proxy.__init__(self, manager)
        self.node = node
        self.nodeType = nodeType
        self.mapattrs(node, {'contents':'childNodes'} )

class SpecialNode(Node):
    def __init__(self, manager, node):
        self.childNodes = []
        Node.__init__(self, manager, node, {'Doctype':xml.dom.Node.DOCUMENT_TYPE_NODE}[node.__class__.__name__] )

class Document(Node):
    def __init__(self, manager, doc):
        Node.__init__(self, manager, doc, xml.dom.Node.DOCUMENT_NODE)

def parse(content):
    pm = webdombase.ProxyManager({ Document : 'BeautifulSoup', SpecialNode: ['Doctype']},
                   { webdombase.ContainerProxy : [ 'list'] },
                   ['str','int'] )
    return pm.get(bs4.BeautifulSoup(content, 'html5lib'))
