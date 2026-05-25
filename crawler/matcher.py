import re
import urllib.parse

class Rule:
    def __init__(self):
        self.host = None
        self.path = None
        self.weight = 0

class Type:
    def __init__(self):
        self.ltype = ''
        self.default = 0
        self.rules = []

    def get_weight(self, purl):
        for r in self.rules:
            if r.host.match(purl.hostname) != None and r.path.match(purl.path) != None:
                return r.weight
        return self.default

class Matcher:
    def __init__(self):
        self.default = 0
        self.types = {}
        self.urls = []

    def get_weight(self, link):
        purl = urllib.parse.urlparse(link.url)
        if purl.scheme != 'https':
            return 0
        if link.usage in self.types:
            return self.types[link.usage].get_weight(purl)
        return self.default

    def load(self, yrules):
        if 'default' in yrules:
            self.default = yrules['default']
        if 'types' in yrules:
            for yt in yrules['types']:
                self.load_type(yt)

    def load_type(self, ytype):
        ltype = Type()
        ltype.ltype = ytype['type']
        if 'weight' in ytype:
            ltype.default = ytype['weight']
        if 'urls' in ytype:
             for yurl in ytype['urls']:
                self.load_url(ltype, yurl)
        self.types[ltype.ltype] = ltype

    def load_url(self, ltype, yurl):
        rule = Rule()
        rule.host = self.load_match(yurl, 'host')
        rule.path = self.load_match(yurl, 'path')
        rule.weight = yurl['weight']
        ltype.rules.append(rule)

    def load_match(self, yurl, key):
        if key in yurl:
            return re.compile(yurl[key])
        else:
            return re.compile('.*')
