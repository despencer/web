import os
import textdoc

class MarkdownWriter:
    def __init__(self, filename, target):
        self.basedir = os.path.dirname(filename)
        self.filename = os.path.basename(filename)
        self.target = target
        self.imagecount = 0
        self.listindent = 0

    def write(self, document):
        self.target.write(f'# {document.title}\n\n')
        for b in document.body:
            self.write_section(b)

    def write_section(self, section):
        if section.header != None and section.level > 0:
            self.target.write(f"{'#'*section.level} {section.header}\n\n")
        content = section.content
        for item in content.items:
            if isinstance(item, textdoc.Para):
                self.write_para(item)
            if isinstance(item, textdoc.List):
                self.write_list(item)
            if isinstance(item, textdoc.Table):
                self.write_table(item)
            if isinstance(item, textdoc.Image):
                self.write_image(item)

    def write_para(self, para):
        if para.style == textdoc.Style.BlockQuote:
            self.target.write('>')
        self.write_runs(para.runs)
        self.target.write('\n\n')

    def isempty(self, runs):
        for run in runs:
            if isinstance(run, textdoc.Run):
                if len(run.text.strip()) > 0:
                    return False
            if isinstance(run, textdoc.Link):
                if not self.isempty(run.runs):
                    return False
        return True

    def write_runs(self, runs):
        for run in runs:
            if isinstance(run, textdoc.Run):
                self.write_run(run)
            if isinstance(run, textdoc.Link):
                self.write_link(run)
            if isinstance(run, textdoc.Image):
                self.write_image(run)

    def write_run(self, run):
        if run.style == textdoc.Style.Strong:
            self.target.write(f'**{run.text}**')
        elif run.style == textdoc.Style.Emphasis:
            self.target.write(f'*{run.text}*')
        elif run.style == textdoc.Style.StrikeThrough:
            self.target.write(f'~~{run.text}~~')
        elif run.style == textdoc.Style.Code:
            if '\n' in run.text:
                self.target.write(f'\n```{run.language}\n{run.text}\n```')
            else:
                self.target.write(f'```{run.text}```')
        else:
            self.target.write(run.text)

    def write_link(self, link):
        if not self.isempty(link.runs):
            self.target.write('[')
            self.write_runs(link.runs)
            self.target.write(f']({link.href})')

    def write_list(self, alist):
        itemno = alist.listtype
        for item in alist.items:
            if isinstance(item, textdoc.List):
                self.listindent += 4
                self.write_list(item)
                self.listindent -= 4
            else:
                if isinstance(itemno, int):
                    prefix = f'{itemno}. '
                    itemno += 1
                else:
                    prefix = itemno + ' '
                prefix = (' '*self.listindent) + prefix
                self.target.write(prefix)
                self.write_para(item)

    def write_table(self, table):
        self.write_table_row(table.header)
        self.target.write('|')
        for c in table.header.cells:
            self.target.write('----|')
        self.target.write('\n')
        for r in table.rows:
            self.write_table_row(r)
        self.target.write('\n')

    def write_table_row(self, row):
        self.target.write('|')
        for c in row.cells:
            self.write_runs(c.runs)
            self.target.write('|')
        self.target.write('\n')

    def write_image(self, image):
        self.imagecount += 1
        imageref = f'{self.filename}-{self.imagecount}.{image.format}'
        with open(self.basedir + '/' + imageref, 'wb') as f:
            f.write(image.data)
        self.target.write(f'![]({imageref})\n\n')
