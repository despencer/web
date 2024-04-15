
class NodeProxy:
    def __init__(self, node):
        self.node = node

class Window:
    def __init__(self):
        pass

def setupcontext(context, dom):
    context.add( {'document':NodeProxy(dom), 'window':Window() } )