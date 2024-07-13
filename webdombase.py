class Proxy:
    def __init__(self, manager):
        self.manager = manager

    def mapattrs(self, obj, attrs):
        for k,v in attrs.items():
            if hasattr(obj, k):
                setattr(self, v, self.manager.get(getattr(obj, k)))

class ContainerProxy(Proxy):
    def __init__(self, manager, collection):
        Proxy.__init__(self, manager)
        self.collection = collection

    def __iter__(self):
        for n in self.collection:
            yield self.manager.get(n)

class ProxyManager:
    def __init__(self, classes, containers, passthrough):
        self.proxies = {}
        self.back = {}
        self.proxyclasses = self.makelookup(classes)
        self.proxyconts = self.makelookup(containers)
        self.passclasses = passthrough

    def get(self, obj):
        if obj == None:
            return None
        clsname = obj.__class__.__name__
        if clsname in self.proxyconts:
            return self.proxyconts[clsname](self, obj)
        if obj in self.proxies:
            return self.proxies[obj]
        if clsname in self.passclasses:
            return obj
        if clsname in self.proxyclasses:
            self.proxies[obj] = self.proxyclasses[clsname](self, obj)
            self.back[ self.proxies[obj] ] = obj
            return self.proxies[obj]
        raise Exception( 'Unknown class ' + clsname + ' for ProxyManager')

    def restore(self, obj):
        if obj in self.back:
            return self.back[obj]
        return obj

    def makelookup(self, params):
        lookup = {}
        for k,v in params.items():
            if isinstance(v, list):
                for c in v:
                    lookup[c] = k
            else:
                lookup[v] = k
        return lookup


class EventTarget:
    def addEventListener(self, evtype, listener, *opt):
        pass


class DomEvent:
    def __init__(self, jstype):
        self.jstype = jstype

    def initCustomEvent(self, name, canBubble, cancelable, detail):
        pass
