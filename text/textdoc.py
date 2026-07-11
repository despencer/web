class Document:
    def __init__(self):
        self.title = ''
        self.body = []

    def add_section(self):
        section = Section()
        self.body.append(section)
        return section

class Section:
    def __init__(self):
        self.header = None
        self.level = 0
        self.content = Content()

class Style:
    def __init__(self):
        self.strong = False

class Content:
    def __init__(self):
        self.items = []

    def add_para(self):
        para = Para()
        self.items.append(para)
        return para

    def add_list(self):
        alist = List()
        self.items.append(alist)
        return alist

class Para:
    def __init__(self):
        self.runs = [ Run() ]
        self.style = Style.Regular

    def get_current_style(self):
        return self.runs[-1].style

    def add_run(self, style):
        arun = Run()
        arun.style = style
        self.runs.append(arun)

    def add_string(self, astr):
        self.runs[-1].text += astr

    def add_link(self, href):
        alink = Link()
        alink.href = href
        nextrun = Run()
        nextrun.style = self.runs[-1].style
        self.runs.append(alink)
        self.runs.append(nextrun)
        return alink

class Run:
    def __init__(self):
        self.style = Style.Regular
        self.text = ''

class Link:
    def __init__(self):
        self.style = Style.Link
        self.runs = [ Run() ]
        self.href = ''

    def add_string(self, astr):
        self.runs[-1].text += astr

class List:
    def __init__(self):
        self.items = []

    def add_item(self):
        para = Para()
        self.items.append(para)
        return para

class Style:
    Regular = 0
    Strong = 1
    Emphasis = 2
    Code = 0x10
    Link = 0x20
    BlockQuote = 0x100
