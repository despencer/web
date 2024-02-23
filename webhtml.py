import xml.dom

class HtmlPrettyPrinter:
    def __init__(self, doc, out):
        self.doc = doc
        self.out = out
        self.indent = 4
        self.formatter = { xml.dom.Node.ELEMENT_NODE : self.formatnode, xml.dom.Node.TEXT_NODE : self.formattext,
                           xml.dom.Node.CDATA_SECTION_NODE : self.formattext, xml.dom.Node.COMMENT_NODE : self.formattext,
                           xml.dom.Node.DOCUMENT_NODE : self.formatdoc, xml.dom.Node.DOCUMENT_TYPE_NODE : self.formatdoc }

    def formatattribute(self, attr):
        return '{0}="{1}"'.format(attr.name, attr.value)

    def formatnode(self, node):
        ret = '<{0}'.format(node.tagName)
        for i in range(node.attributes.length):
            ret += ' ' + self.formatattribute(node.attributes.item(i))
        return ret+'>'

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
