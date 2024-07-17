import bs4
import xml.dom
import webdombase

class Node(webdombase.Proxy):
    def __init__(self, manager, node, nodeType):
        webdombase.Proxy.__init__(self, manager)
        self.node = node
        self.nodeType = nodeType
        self.childNodes = []
        self.mapattrs(node, {'contents':'childNodes'} )

class SpecialNode(Node):
    def __init__(self, manager, node):
        Node.__init__(self, manager, node,
            {'Doctype':xml.dom.Node.DOCUMENT_TYPE_NODE, 'Comment':xml.dom.Node.COMMENT_NODE}
                   [node.__class__.__name__] )

class Text(Node):
    def __init__(self, manager, node):
        Node.__init__(self, manager, node, xml.dom.Node.TEXT_NODE)

class Attribute(Node):
    def __init__(self, manager, name, value):
        Node.__init__(self, manager, self, xml.dom.Node.ATTRIBUTE_NODE)
        self.name = name
        self.value = value

class Element(Node):
    def __init__(self, manager, node):
        Node.__init__(self, manager, node, xml.dom.Node.ELEMENT_NODE)
        self.nodeName = node.name
        self.attributes = {}
        for k,v in node.attrs.items():
            self.attributes[k] = Attribute(self.manager, k,v)

class DocumentFragment(webdombase.Proxy):
    def __init__(self, manager, document):
        webdombase.Proxy.__init__(self, manager)
        self.nodeType = xml.dom.Node.DOCUMENT_FRAGMENT_NODE
        self.document = document

    def createElement(self, tagname):
        return self.document.createElement(tagname)

class Document(Node):
    def __init__(self, manager, doc):
        Node.__init__(self, manager, doc, xml.dom.Node.DOCUMENT_NODE)

    def createElement(self, tagname):
        return self.manager.get(self.node.new_tag(tagname))

    def createDocumentFragment(self):
        return DocumentFragment(self.manager, self.node)

    def createHTMLDocument(self, title):
        return self.manager.get(bs4.BeautifulSoup('<html><head><title>' + title + '</title></head><body></body></html>', 'html5lib', multi_valued_attributes = None))


def parse(content):
    pm = webdombase.ProxyManager({ Document : 'BeautifulSoup', SpecialNode: ['Doctype','Comment'], Element: 'Tag', Text: 'NavigableString'},
                   { webdombase.ContainerProxy : [ 'list'] },
                   ['str','int'] )
    return pm.get(bs4.BeautifulSoup(content, 'html5lib', multi_valued_attributes = None))
