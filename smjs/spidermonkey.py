import smjs

class Context:
    def __init__(self):
        self.jsfuncs = {}

    def open(self):
        smjs.open_context(self)
        smjs.init_context(self)

    def close(self):
       smjs.close_context(self)

    def execute(self, jscode):
       smjs.execute(self, jscode)

    def add(self, globs):
       for name, obj in globs.items():
            if callable(obj):
                self.jsfuncs[name] = obj
                smjs.add_globalfunction(self, name)
            else:
                smjs.add_globalobject(self, name, obj)
                for name in vars(obj):
                    if name[0] != '_':
                        smjs.add_objectproperty(self, obj, name)

    def funccall(self, funcname, args):
       return self.jsfuncs[funcname](*args)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, extype, exvalue, extrace):
        self.close()

def connect():
    return Context()

def shutdown():
    smjs.shutdown()

import atexit
atexit.register(shutdown)