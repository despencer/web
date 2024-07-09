class ContainerProxy:
    def __init__(self, manager, collection):
        self.manager = manager
        self.collection = collection

    def __iter__(self):
        return iter(self.collection)

class ProxyManager:
    def __init__(self, nodeproxy, classes, containers, passthrough):
        self.proxies = {}
        self.back = {}
        self.nodeproxy = nodeproxy
        self.proxyclasses = classes
        self.proxyconts = containers
        self.passclasses = passthrough

    def get(self, obj):
        if obj == None:
            return None
        if obj.__class__.__name__ in self.proxyconts:
            return ContainerProxy(self, obj)
        if obj in self.proxies:
            return self.proxies[obj]
        if obj.__class__.__name__ in self.passclasses:
            return obj
        if obj.__class__.__name__ in self.proxyclasses:
            self.proxies[obj] = self.nodeproxy(self, obj)
            self.back[ self.proxies[obj] ] = obj
            return self.proxies[obj]
        raise Exception( 'Unknown class ' + obj.__class__.__name__ + ' for ProxyManager')

    def restore(self, obj):
        if obj in self.back:
            return self.back[obj]
        return obj

class EventTarget:
    def addEventListener(self, evtype, listener, *opt):
        pass


class DomEvent:
    def __init__(self, jstype):
        self.jstype = jstype

    def initCustomEvent(self, name, canBubble, cancelable, detail):
        pass
