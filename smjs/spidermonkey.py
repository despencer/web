import smjs

class Proxy:
    def __init__(self, capsule):
        self.capsule = capsule

class Context:
    def __init__(self, globj):
        self.globj = globj
        self.proxies = []

    def open(self):
        smjs.open_context(self)
        smjs.init_context(self)

    def close(self):
        smjs.close_context(self)

    def execute(self, jscode):
        smjs.execute(self, jscode)

    def funccall(self, obj, funcname, args):
        return obj._smjsfuncs_[funcname](*args)

    def calljsfunc(self, funcproxy):
        print(funcproxy)

    def objectsync(self, obj):
        ''' Fill the JavaScript object with Python project attributes '''
        if not hasattr(obj, '_smjsfuncs_'):
            obj._smjsfuncs_ = {}
        for name in dir(obj):
            if name[0] != '_':
                attr = getattr(obj, name)
                if callable(attr):
                    obj._smjsfuncs_[name] = attr
                    smjs.add_objectfunction(self, obj, name)
                else:
                    smjs.add_objectproperty(self, obj, name)

    def createproxy(self, capsule):
        ''' Creates a proxy python object for JS  object and stores it into list in order not to be garbage collected '''
        proxy = Proxy(capsule)
        self.proxies.append(proxy)
        return proxy

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, extype, exvalue, extrace):
        self.close()

def connect(globj):
    return Context(globj)

def shutdown():
    smjs.shutdown()

import atexit
atexit.register(shutdown)