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

    def add_list(self, listtype):
        alist = List()
        alist.listtype = listtype
        self.items.append(alist)
        return alist

    def add_table(self):
        table = Table()
        self.items.append(table)
        return table

    def add_image(self, format, data):
        image = Image(format, data)
        self.items.append(image)
        return image

class Para:
    def __init__(self):
        self.runs = [ Run() ]
        self.style = Style.Regular

    def get_current_style(self):
        return self.runs[-1].style

    def last_run(self):
        return self.runs[-1]

    def add_run(self, style):
        arun = Run()
        arun.style = style
        self.runs.append(arun)

    def add_string(self, astr):
        self.runs[-1].text += astr

    def add_link(self, href):
        alink = Link()
        alink.href = href
        return self.add_item(alink)

    def add_image(self, format, data):
        image = Image(format, data)
        return self.add_item(image)

    def add_content(self):
        content = Content()
        return self.add_item(content)

    def add_item(self, item):
        nextrun = Run()
        nextrun.style = self.runs[-1].style
        self.runs.append(item)
        self.runs.append(nextrun)
        return item

class Run:
    def __init__(self):
        self.style = Style.Regular
        self.text = ''
        self.language = ''

class Link:
    def __init__(self):
        self.style = Style.Link
        self.runs = [ Run() ]
        self.href = ''

    def add_string(self, astr):
        self.runs[-1].text += astr

class List:
    def __init__(self):
        self.listtype = '-'
        self.items = []

    def add_item(self):
        para = Para()
        self.items.append(para)
        return para

    def add_list(self, listtype):
        alist = List()
        alist.listtype = listtype
        self.items.append(alist)
        return alist

class Image:
    def __init__(self, format, data):
        self.format = format
        self.data = data

class Table:
    def __init__(self):
        self.header = Row()
        self.rows = []

    def add_row(self):
        row = Row()
        self.rows.append(row)
        return row

class Row:
    def __init__(self):
        self.cells = []

    def size(self):
        return len(self.cells)

    def add_cell(self):
        para = Para()
        self.cells.append(para)
        return para

class Style:
    Regular = 0
    Strong = 1
    Emphasis = 2
    StrikeThrough = 4
    Code = 0x10
    Link = 0x20
    BlockQuote = 0x100
