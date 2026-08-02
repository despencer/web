import yaml
import webhtml
import sys
import os
sys.path.append(os.path.expanduser('~/dev/datan'))
from bs4 import Tag, NavigableString, Comment
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

    def storage(self):
        return self.document.harstorage

    def add_section(self):
       return self.document.add_section()

    def add_header(self, level, header):
        self.section.level = level
        self.section.header = header

    def add_para(self):
        return ParaBuilder(self, self.section.content.add_para())

    def add_list(self,listtype):
        return ListBuilder(self, self.section.content.add_list(listtype))

    def add_table(self):
        return TableBuilder(self, self.section.content.add_table())

    def add_image(self, filetype, data):
        self.section.content.add_image(filetype, data)

    def add_link(self, href):
        return ParaBuilder(self, self.section.content.add_para()).add_link(href)

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
        return ParaBuilder(self.section, self.alist.add_item())

    def add_list(self, listtype):
        return ListBuilder(self.section, self.alist.add_list(listtype))

class LinkBuilder:
    def __init__(self, alink):
        self.para = alink

class TableBuilder:
    def __init__(self, section, atable):
        self.section = section
        self.table = atable

    def get_header(self):
        if self.table.header.size() > 0:
            print('Table header repeats, overwritten')
        return TableRowBuilder(self, self.table.header)

    def add_row(self):
        return TableRowBuilder(self, self.table.add_row())

class TableRowBuilder:
    def __init__(self, table, row):
        self.table = table
        self.row = row

    def check_header(self):
        return (self.row == self.table.table.header)

    def check_body(self):
        return not self.check_header()

    def add_cell(self):
        return TableCellBuilder(self, self.row.add_cell())

class TableCellBuilder:
    def __init__(self, row, cell):
        self.row = row
        self.para = cell

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

class NodeReplacer:
    def __init__(self):
        self.source = NodeLocator()
        self.target = 'p'

    def match(self, node):
        return self.source.match(node)

    def load(self, ynode):
        self.source.load(ynode['source'])
        self.target = ynode['target']['node']

class BodyMaker:
    def __init__(self):
        self.start = NodeLocator()
        self.exclude = []
        self.replace = []
        self.code = ''

    def make(self, rootnode, builder):
        for n in self.start.find(rootnode):
            self.make_node(n, builder.add_section())

    def make_node(self, node, target):
        self.walk_nodes(node, {'div': self.make_node, 'p':self.make_para, 'ul': self.make_list,  'ol': self.make_list,
                               'blockquote': self.make_block_quote, 'table': self.make_table, 'figure': self.make_node,
                               'img': self.make_image, 'header': self.make_node, 'button': self.skip, 'article': self.make_node,
                               'a': self.make_link, 'span': self.make_node,
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

    def make_block_quote_inside(self, pnode, pbuilder):
        bqbuilder = pbuilder.section.add_para()
        bqbuilder.para.style = textdoc.Style.BlockQuote
        self.make_para_contents(pnode, bqbuilder)
        pbuilder.para = pbuilder.section.add_para().para

    def make_para_contents(self, pnode, pbuilder):
        self.walk_nodes(pnode, {'code': self.make_code, 'strong': self.make_strong, 'em': self.make_emphasis,
                                'br': lambda x,y: y.para.add_string('\n'), 'u':self.make_para_contents,
                                'a': self.make_link, 'header': self.make_para_contents, 'blockquote': self.make_block_quote_inside,
                                'mark': self.make_para_contents, 'span': self.make_para_contents, 'div': self.make_para_contents,
                                'pre': self.make_para_contents, 'p': self.make_para_contents, 'button': self.skip, 
                                '$default':lambda x,y:print(f'Unknown node {x.name} in para node: {str(x)[:70]}'),
                               '$string': lambda x,y: y.para.add_string(x.string) }, pbuilder )

    def make_list(self, lnode, nbuilder):
        listtype = '-'
        if lnode.name == 'ol':
            listtype = 1
        self.make_list_contents(lnode, nbuilder.add_list( listtype ))

    def make_list_contents(self, lnode, lbuilder):
        self.walk_nodes(lnode, {'li':self.make_list_item, 'section':self.make_list_contents, 'ul':self.make_list,
                                '$default':lambda x,y:print(f'Unknown node {x.name} in list node: {str(x)[:70]}'),
                               '$string': self.check_hanging }, lbuilder )

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
        href = ''
        if 'href' in lnode.attrs:
            href = lnode['href']
        self.make_link_contents(lnode, pbuilder.add_link(href))

    def make_link_contents(self, lnode, lbuilder):
        self.walk_nodes(lnode, {'code': lambda x,y: y.para.add_string(''.join(x.strings)),
                                'time': self.make_link_contents,
                               '$default':lambda x,y:print(f'Node {x.name} in xref node: {str(x)[:70]}'),
                               '$string': lambda x,y: y.para.add_string(x.string) }, lbuilder )

    def make_code(self, cnode, pbuilder):
        style = pbuilder.para.get_current_style()
        pbuilder.para.add_run(textdoc.Style.Code)
        if 'class' in cnode.attrs:
            pbuilder.para.last_run().language = cnode['class']
        else:
            pbuilder.para.last_run().language = self.code
        self.make_code_contents(cnode, pbuilder)
        pbuilder.para.add_run(style)

    def make_code_contents(self, cnode, cbuilder):
        self.walk_nodes(cnode, {'span': self.make_code_contents, 'br': lambda x,y: y.para.add_string('\n'),
                                '$default':lambda x,y:print(f'Node {x.name} in code node: {str(x)[:70]}'),
                               '$string': lambda x,y: y.para.add_string(x.string) }, cbuilder )

    def make_section(self, snode, target):
        self.make_node(snode, target.add_section())

    def make_table(self, tnode, builder):
        self.walk_nodes(tnode, {'thead': self.make_table_contents, 'tbody': self.make_table_contents,
                                '$default':lambda x,y:print(f'Node {x.name} in table node: {str(x)[:70]}'),
                               '$string': self.check_hanging }, builder.add_table() )

    def make_table_contents(self, tnode, tbuilder):
        self.walk_nodes(tnode, {'tr': self.make_table_row,
                                '$default':lambda x,y:print(f'Node {x.name} in table: {str(x)[:70]}'),
                               '$string': self.check_hanging }, tbuilder )

    def make_table_row(self, trow, tbuilder):
        if trow.parent.name == 'thead':
            rbuilder = tbuilder.get_header()
        else:
            rbuilder = tbuilder.add_row()
        self.walk_nodes(trow, {'th': self.make_table_cell, 'td': self.make_table_cell,
                                '$default':lambda x,y:print(f'Node {x.name} in table body: {str(x)[:70]}'),
                               '$string': self.check_hanging }, rbuilder )

    def make_table_cell(self, tcell, rbuilder):
        if tcell.name == 'th':
            rbuilder.check_header()
        else:
            rbuilder.check_body()
        self.make_para_contents(tcell, rbuilder.add_cell())

    def make_image(self, inode, builder):
        if 'src' not in inode.attrs:
            print(f'No source attribute in image, {str(inode)[:90]}')
            return
        image = builder.storage().get_response_byurl(inode['src'])
        if image == None:
            print(f'No image in har storage for {inode['src']}')
            return
        builder.add_image(image.content_type().split('/')[1], image.content)

    def walk_nodes(self, anode, handlers, target):
        for c in anode.children:
            if isinstance(c, Tag):
                done = False
                for ex in self.exclude:
                    if ex.match(c):
                        done = True
                if not done:
                    name = c.name
                    for repl in self.replace:
                        if repl.match(c):
                            name = repl.target
                    if name in handlers:
                        handlers[name](c, target)
                    else:
                        handlers['$default'](c, target)
            if type(c) is NavigableString:
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
        if 'replace' in ybody:
            for yrepl in ybody['replace']:
                repl = NodeReplacer()
                repl.load(yrepl)
                self.replace.append(repl)
        if 'code' in ybody:
            self.code = ybody['code']

class MarkdownMaker:
    def __init__(self):
        self.header = HeaderLocator()
        self.bodies = []

    def make(self, rootnode, harstorage, filename, target):
        doc = textdoc.Document()
        self.header.extract(rootnode, doc)
        builder = DocumentBuilder(doc, harstorage)
        for b in self.bodies:
            b.make(rootnode, builder)
        mdwriter.MarkdownWriter(filename, target).write(doc)

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
