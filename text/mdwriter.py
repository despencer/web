import textdoc

class MarkdownWriter:
    def __init__(self, target):
        self.target = target

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

    def write_para(self, para):
        self.write_runs(para.runs)
        self.target.write('\n\n')

    def write_runs(self, runs):
        for run in runs:
            if isinstance(run, textdoc.Run):
                self.write_run(run)
            if isinstance(run, textdoc.Link):
                self.write_link(run)

    def write_run(self, run):
        if run.style == textdoc.Style.Strong:
            self.target.write(f'**{run.text}**')
        elif run.style == textdoc.Style.Code:
            self.target.write(f'```{run.text}```')
        else:
            self.target.write(run.text)

    def write_link(self, link):
        self.target.write('[')
        self.write_runs(link.runs)
        self.target.write(f']({link.href})')

    def write_list(self, alist):
        for item in alist.items:
            self.target.write('- ')
            self.write_para(item)
