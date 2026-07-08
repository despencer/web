import yaml
import webhtml
import sys
import os
sys.path.append(os.path.expanduser('~/dev/datan'))
from bs4 import Tag, NavigableString
import textdoc
import mdwriter

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

    def make(self, rootnode, target):
        for n in self.start.find(rootnode):
            self.make_node(n, target.add_section())

    def make_node(self, node, target):
        for ex in self.exclude:
            if ex.match(node):
                return
        self.walk_nodes(node, {'div': self.make_node, 'p':self.make_para, 'ul':self.make_list,
                               '$default':lambda x,y:print(f'Unknown node {x.name} in node'),
                               '$string': self.check_hanging }, target )

    def make_para(self, pnode, target):
        self.make_para_contents(pnode, target.add_para())

    def make_para_contents(self, pnode, target):
        self.walk_nodes(pnode, {'code': self.make_code, 'strong': self.make_strong, 'a': self.make_link,
                                '$default':lambda x,y:print(f'Unknown node {x.name} in para node: {str(x)[:50]}'),
                               '$string': lambda x,y: y.add_string(x.string) }, target )

    def make_list(self, lnode, target):
        self.walk_nodes(lnode, {'li':self.make_list_item, '$default':lambda x,y:print(f'Unknown node {x.name} in list node'),
                               '$string': self.check_hanging }, target.add_list() )

    def make_list_item(self, linode, target):
        self.make_para_contents(linode, target.add_item())

    def make_strong(self, pnode, target):
        target.add_run(textdoc.Style.Strong)
        self.make_para_contents(pnode, target)
        target.add_run(textdoc.Style.Regular)

    def make_link(self, lnode, target):
        self.walk_nodes(lnode, {'$default':lambda x,y:print(f'Node {x.name} in xref node'),
                               '$string': lambda x,y: y.add_string(x.string) }, target.add_link(lnode['href']) )

    def make_code(self, cnode, target):
        style = target.get_current_style()
        target.add_run(textdoc.Style.Code)
        self.walk_nodes(cnode, {'$default':lambda x,y:print(f'Node {x.name} in code node'),
                               '$string': lambda x,y: y.add_string(x.string) }, target )
        target.add_run(style)

    def walk_nodes(self, anode, handlers, target):
        for c in anode.children:
            if isinstance(c, Tag):
                if c.name in handlers:
                    handlers[c.name](c, target)
                else:
                    handlers['$default'](c, target)
            if isinstance(c, NavigableString):
                handlers['$string'](c, target)

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

    def make(self, rootnode, target):
        doc = textdoc.Document()
        self.header.extract(rootnode, doc)
        for b in self.bodies:
            b.make(rootnode, doc)
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
