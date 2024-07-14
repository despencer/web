import xml.dom
import urllib.parse

class AttrNode:
    ''' Original xml.dom attribute lacks references to the node container '''
    def __init__(self, node, attr):
        self.nodeType = xml.dom.Node.ATTRIBUTE_NODE
        self.parentNode = node
        self.nodeName = attr.name
        self.nodeValue = attr.value

class HtmlLink:
    ''' A link from HTML document to other resources. usage: value of Sec-Fetch-Dest, link: original link, url: reconstructed url '''
    def __init__(self, usage, link, url):
        self.usage = usage
        self.link = link
        self.url = url

class HtmlLinkExtractor:
    def __init__(self, doc, base):
        self.doc = doc
        self.base = base
        self.links = []
        self.index = []
        self.attrs = {'script' : ['src'], 'link': ['href'], 'img': ['src'] }
        self.usage = {'script':'script', 'link':'$rel', 'link.rel.icon':'image', 'link.rel.stylesheet':'css', 'img':'image'}

    def addlink(self, tagname, attrvalue, node):
        url = urllib.parse.urljoin(self.base, attrvalue)
        if url not in self.index:
            usage = self.usage[tagname]
            if usage[0] == '$':
                attrname = usage[1:]
                usage = self.usage[ '{0}.{1}.{2}'.format(tagname, attrname, node.attributes[attrname].value) ]
            self.links.append( HtmlLink(usage, attrvalue, url) )
            self.index.append(url)

    def extract(self):
        for node in traverse(self.doc):
            if node.nodeType == xml.dom.Node.ATTRIBUTE_NODE and node.parentNode.nodeName in self.attrs and node.nodeName in self.attrs[node.parentNode.nodeName]:
                self.addlink(node.parentNode.nodeName, node.nodeValue, node.parentNode)
        return self.links

class HtmlPrettyPrinter:
    def __init__(self, doc, out):
        self.doc = doc
        self.out = out
        self.indent = 4
        self.formatter = { xml.dom.Node.ELEMENT_NODE : self.formatnode, xml.dom.Node.TEXT_NODE : self.formattext,
                           xml.dom.Node.CDATA_SECTION_NODE : self.formattext, xml.dom.Node.COMMENT_NODE : self.formatcomment,
                           xml.dom.Node.DOCUMENT_NODE : self.formatdoc, xml.dom.Node.DOCUMENT_TYPE_NODE : self.formatdoc }

    def formatattribute(self, attr):
        return '{0}="{1}"'.format(attr.name, attr.value)

    def formatnode(self, node):
        ret = '<{0}'.format(node.tagName)
        for i in range(node.attributes.length):
            ret += ' ' + self.formatattribute(node.attributes.item(i))
        return ret+'>'

    def formatcomment(self, text):
        return '<!-- {0} -->'.format(text.data.strip())

    def formattext(self, text):
        return text.data.strip()

    def formatdoc(self, doc):
        return doc.nodeName

    def printnode(self, indent, node):
        text = self.formatter[node.nodeType](node)
        if text == '':
            return
        if node.nodeType == xml.dom.Node.ELEMENT_NODE and node.tagName.lower() in ['script','style']:
            self.out.write('{0}{1}\n'.format(''.ljust(indent), text))
        elif node.nodeType == xml.dom.Node.ELEMENT_NODE and len(node.childNodes) == 1 and node.childNodes[0].nodeType == xml.dom.Node.TEXT_NODE:
            self.out.write('{0}{1} {2}\n'.format(''.ljust(indent), text, self.formattext(node.childNodes[0])))
        else:
            self.out.write('{0}{1}\n'.format(''.ljust(indent), text))
            for c in node.childNodes:
                self.printnode(indent+self.indent, c)

    def print(self):
        self.printnode(0, self.doc)

def prettyprint(doc, st):
    HtmlPrettyPrinter(doc,st).print()

def traverse(node):
    yield node
    if node.nodeType == xml.dom.Node.ELEMENT_NODE:
        for a in node.attributes.values():
            yield AttrNode(node, a)
    for c in node.childNodes:
        yield from traverse(c)

def getnodepath(node):
    path = []
    while node.parentNode != None:
        path.append(node)
        node = node.parentNode
    path.reverse()
    return path

def getlinks(doc, base):
    return HtmlLinkExtractor(doc, base).extract()
