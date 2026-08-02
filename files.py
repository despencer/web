import os
import webhttp

image_extensions = { 'png':'image/png', 'jpg':'image/jpeg', 'jpg':'image/jpeg' }

class FileStorage:
    def __init__(self, filename):
        self.basedir = os.path.dirname(filename)
        if self.basedir == '':
            self.basedir = '.'
        self.cache = {}
        self.filename = filename
        with open(filename, 'r', encoding='utf-8') as f:
            self.response = webhttp.HttpResponse()
            self.response.content = f.read()
            self.response.headers['content-type'] = 'text/html; charset=utf-8'

    def get_response_byurl(self, url):
        fileurl = self.basedir + '/' + url
        if os.path.isfile(fileurl):
            return self.load_file(fileurl)
        return None

    def load_file(self, filename):
        if filename in self.cache:
            return self.cache[filename]
        ext = os.path.splitext(filename)[1][1:]
        if ext in image_extensions:
            with open(filename, 'rb') as f:
                response = webhttp.HttpResponse()
                response.content = f.read()
                response.headers['content-type'] = image_extensions[ext]
                self.cache[filename] = response
                return response


def load(filename):
    return FileStorage(filename)