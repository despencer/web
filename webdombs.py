import bs4
import xml.dom
import webdombase

class Node(webdombase.Proxy):
    def __init__(self, manager, node, nodeType):
        webdombase.Proxy.__init__(self, manager)
        self.node = node
        self.nodeType = nodeType
        self.childNodes = self.manager.get(node.contents)

class Document(Node):
    def __init__(self, manager, doc):
        Node.__init__(self, manager, doc, xml.dom.Node.DOCUMENT_NODE)

def parse(content):
    pm = webdombase.ProxyManager({ Document : 'BeautifulSoup' },
                   { webdombase.ContainerProxy : [ 'list'] },
                   ['str','int'] )
    return pm.get(bs4.BeautifulSoup(content, 'html5lib'))
