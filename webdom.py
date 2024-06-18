class NodeProxy:
    def __init__(self, manager, node):
        self.manager = manager
        self.node = node
        self.checkattrs( ['nodeType', 'documentElement'] )

    def checkattrs(self, names):
        for name in names:
            if hasattr(self.node, name):
                setattr(self, name, self.manager.get(getattr(self.node, name)))

    def appendChild(self, node):
        node = self.manager.restore(node)
        return self.manager.get(self.node.appendChild(node))

    def createElement(self, tagname):
        return self.manager.get(self.node.createElement(tagname))

    def createDocumentFragment(self):
        return self.manager.get(self.node.createDocumentFragment())

    def setAttribute(self, name, value):
        self.node.setAttribute(name, value)

    def cloneNode(self, deep):
        return self.manager.get(self.node.cloneNode(deep))

class ProxyManager:
    def __init__(self):
        self.proxies = {}
        self.back = {}
        self.proxyclasses = ['Node', 'DocumentFragment', 'Attr', 'Element', 'CharacterData',
                   'Text', 'CDATASection', 'DocumentType', 'Entity', 'Notation', 'ElementInfo', 'Document']
        self.passclasses = ['str','int']

    def get(self, obj):
        if obj in self.proxies:
            return self.proxies[obj]
        if obj.__class__.__name__ in self.passclasses:
            return obj
        if obj.__class__.__name__ in self.proxyclasses:
            self.proxies[obj] = NodeProxy(self, obj)
            self.back[ self.proxies[obj] ] = obj
            return self.proxies[obj]
        raise Exception( 'Unknown class ' + obj.__class__.__name__ + ' for ProxyManager')

    def restore(self, obj):
        if obj in self.back:
            return self.back[obj]
        return obj

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
    pm = ProxyManager()
    window.document = pm.get(dom)
    return window
