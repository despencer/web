import yaml
import webhtml
import sys
import os
sys.path.append(os.path.expanduser('~/dev/datan'))
from bs4 import Tag, NavigableString
import textdoc
import mdwriter

class DocumentBuilder:
    def __init__(self, document, harstorage):
        self.document = document
        self.harstorage = harstorage

    def add_section(self):
       return SectionBuilder(self, self.document.add_section())

class SectionBuilder:
    def __init__(self, docbuilder, section):
        self.document = docbuilder
        self.section = section

    def add_section(self):
       return self.document.add_section()

    def add_header(self, level, header):
        self.section.level = level
        self.section.header = header

    def add_para(self):
        return ParaBuilder(self, self.section.content.add_para())

    def add_list(self,listtype):
        return ListBuilder(self, self.section.content.add_list(listtype))

class ParaBuilder:
    def __init__(self, section, para):
        self.section = section
        self.para = para

    def add_link(self, href):
        return LinkBuilder(self.para.add_link(href))

class ListBuilder:
    def __init__(self, section, alist):
        self.section = section
        self.alist = alist

    def add_item(self):
        return ParaBuilder(self, self.alist.add_item())

class LinkBuilder:
    def __init__(self, alink):
        self.para = alink

class HeaderLocator:
    def __init__(self):
        self.level = 1
        self.node = 'h1'

    def extract(self, rootnode, target):
        builder = ''
        for n in rootnode.find_all(self.node):
            builder += n.string
        target.title = builder

    def load(self, yheader):
        if 'level' in yheader:
            self.level = yheader['level']
        if 'node' in yheader:
            self.node = yheader['node']

class NodeLocator:
    def __init__(self):
        self.node = 'p'
        self.attrs = {}

    def find(self, node):
        return node.find_all(self.node, attrs=self.attrs)

    def match(self, node):
        if self.node != node.name:
            return False
        for ak, av in self.attrs.items():
            if ak not in node.attrs:
                return False
            if isinstance(node.attrs[ak], list):
                if av not in node.attrs[ak]:
                    return False
            else:
                if av != node.attrs[ak]:
                    return False
        return True

    def load(self, ynode):
        if 'node' in ynode:
            self.node = ynode['node']
        if 'attrs' in ynode:
            self.attrs = ynode['attrs']

class BodyMaker:
    def __init__(self):
        self.start = NodeLocator()
        self.exclude = []

    def make(self, rootnode, builder):
        for n in self.start.find(rootnode):
            self.make_node(n, builder.add_section())

    def make_node(self, node, target):
        self.walk_nodes(node, {'div': self.make_node, 'p':self.make_para, 'ul': self.make_list,  'ol': self.make_list,
                               'blockquote': self.make_block_quote,
                               'section': self.make_section, 'code-block':self.make_para, 'h2': lambda x, y: y.add_header(2, ''.join(x.strings)),
                               'h3': lambda x, y: y.add_header(3, ''.join(x.strings)),
                               '$default':lambda x,y:print(f'Unknown node {x.name} in node: {str(x)[:90]}'),
                               '$string': self.check_hanging }, target )

    def make_section(self, snode, sbuilder):
        self.make_node(n, builder.add_section())

    def make_para(self, pnode, target):
        self.make_para_contents(pnode, target.add_para())

    def make_block_quote(self, pnode, target):
        pbuilder = target.add_para()
        pbuilder.para.style = textdoc.Style.BlockQuote
        self.make_para_contents(pnode, pbuilder)

    def make_para_contents(self, pnode, pbuilder):
        self.walk_nodes(pnode, {'code': self.make_code, 'strong': self.make_strong, 'em': self.make_emphasis,
                                'a': self.make_link,
                                'mark': self.make_para_contents, 'span': self.make_para_contents, 'div': self.make_para_contents,
                                'pre': self.make_para_contents, 'p': self.make_para_contents, 'button': self.skip, 
                                '$default':lambda x,y:print(f'Unknown node {x.name} in para node: {str(x)[:70]}'),
                               '$string': lambda x,y: y.para.add_string(x.string) }, pbuilder )

    def make_list(self, lnode, nbuilder):
        self.walk_nodes(lnode, {'li':self.make_list_item, '$default':lambda x,y:print(f'Unknown node {x.name} in list node'),
                               '$string': self.check_hanging }, nbuilder.add_list( {'ul':'-', 'ol':1}[lnode.name] ) )

    def make_list_item(self, linode, lbuilder):
        self.make_para_contents(linode, lbuilder.add_item())

    def make_strong(self, pnode, pbuilder):
        pbuilder.para.add_run(textdoc.Style.Strong)
        self.make_para_contents(pnode, pbuilder)
        pbuilder.para.add_run(textdoc.Style.Regular)

    def make_emphasis(self, pnode, pbuilder):
        pbuilder.para.add_run(textdoc.Style.Emphasis)
        self.make_para_contents(pnode, pbuilder)
        pbuilder.para.add_run(textdoc.Style.Regular)

    def make_link(self, lnode, pbuilder):
        self.walk_nodes(lnode, {'code': lambda x,y: y.para.add_string(''.join(x.strings)),
                               '$default':lambda x,y:print(f'Node {x.name} in xref node: {str(x)[:70]}'),
                               '$string': lambda x,y: y.para.add_string(x.string) }, pbuilder.add_link(lnode['href']) )

    def make_code(self, cnode, pbuilder):
        style = pbuilder.para.get_current_style()
        pbuilder.para.add_run(textdoc.Style.Code)
        self.make_code_contents(cnode, pbuilder)
        pbuilder.para.add_run(style)

    def make_code_contents(self, cnode, cbuilder):
        self.walk_nodes(cnode, {'span': self.make_code_contents,
                                '$default':lambda x,y:print(f'Node {x.name} in code node: {str(x)[:70]}'),
                               '$string': lambda x,y: y.para.add_string(x.string) }, cbuilder )

    def make_section(self, snode, target):
        self.make_node(snode, target.add_section())

    def walk_nodes(self, anode, handlers, target):
        for c in anode.children:
            if isinstance(c, Tag):
                skip = False
                for ex in self.exclude:
                    if ex.match(c):
                        skip = True
                if not skip:
                    if c.name in handlers:
                        handlers[c.name](c, target)
                    else:
                        handlers['$default'](c, target)
            if isinstance(c, NavigableString):
                handlers['$string'](c, target)

    def skip(self, node, target):
        pass

    def check_hanging(self, snode, target):
        if snode.string.strip() != '':
            print(f'Hanging text {snode.string.strip()}')

    def load(self, ybody):
        self.start.load(ybody['start'])
        if 'exclude' in ybody:
            for yex in ybody['exclude']:
                ex = NodeLocator()
                ex.load(yex)
                self.exclude.append(ex)

class MarkdownMaker:
    def __init__(self):
        self.header = HeaderLocator()
        self.bodies = []

    def make(self, rootnode, harstorage, target):
        doc = textdoc.Document()
        self.header.extract(rootnode, doc)
        builder = DocumentBuilder(doc, harstorage)
        for b in self.bodies:
            b.make(rootnode, builder)
        mdwriter.MarkdownWriter(target).write(doc)

    @classmethod
    def load(cls, yrules):
        maker = cls()
        if 'header' in yrules:
            maker.header.load(yrules['header'])
        for ybody in yrules['body']:
            body = BodyMaker()
            body.load(ybody)
            maker.bodies.append(body)
        return maker

def load(frules):
    with open(frules) as yfile:
        yrules = yaml.load(yfile, Loader=yaml.Loader)
    return MarkdownMaker.load(yrules)
