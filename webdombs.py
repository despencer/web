from bs4 import BeautifulSoup
import webdombase

def parse(content):
    pm = webdombase.ProxyManager({ NodeProxy : 
                   [] },
                   { webdombase.ContainerProxy : [ ] },
                   ['str','int'] )
    return pm.get(BeautifulSoup(htmlfile, 'html5lib'))
