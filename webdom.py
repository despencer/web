class ElementProxy:
    def __init__(self, node):
        self.node = node

class DocumentProxy:
    def __init__(self, node):
        self.node = node
        self.nodeType = node.nodeType
        self.documentElement = ElementProxy(node.documentElement)

    def createElement(self, tagname):
        return ElementProxy(self.node.createElement(tagname))

class Console:
    def log(self, *msg):
        print(*msg)

class Event:
    def __init__(self, args):
        self.func = args[0]
        if len(args) >= 2:
            self.delay = args[1]
        self.args = args[2:]

    def execute(self, jscontext):
        if len(self.args) > 0:
            raise Exception ('Timeout with arguments not yet implemented')
        jscontext.calljsfunc(self.func)

class Window:
    def __init__(self):
        self.window = self
        self.events = []
        self.console = Console()

    def processevents(self, jscontext):
        while len(self.events) > 0:
            self.events.pop(0).execute(jscontext)

    def setTimeout(self, *args):
        self.events.append( Event(args) )

def setupcontext(dom):
    window = Window()
    window.document = DocumentProxy(dom)
    return window
