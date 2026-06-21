import yaml
import webhtml
import sys
import os
sys.path.insert(1, os.path.expanduser('~/dev/datan'))
import parser

class MarkdownWriter:
    def __init__(self, target):
        self.target = target

    def para(self, x):
        self.target.write(str(x)+'\n')

class MarkdownMaker:
    def __init__(self):
        self.parser = None

    def make(self, rootnode, target):
        mdwriter = MarkdownWriter(target)
        self.parser.transform( { 'htmlstream':webhtml.HtmlStream(rootnode), 'mdwriter':mdwriter} )

    @classmethod
    def load(cls, yrules):
        maker = cls()
        maker.parser = parser.loadparser(yrules['transform'], None)
        return maker

def load(frules):
    with open(frules) as yfile:
        yrules = yaml.load(yfile, Loader=yaml.Loader)
    return MarkdownMaker.load(yrules)
