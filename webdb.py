
class UrlTask:
    def __init__(self):
        self.id = None
        self.status = None
        self.origin = None
        self.kind = None
        self.url = None

    @classmethod
    def create(cls, db, url):
        task = cls()
        task.id = db.genid()
        task.status = 'init'
        task.origin = None
        task.kind = 'document'
        task.url = url
        db.execute("INSERT INTO web_url_task (id, status, origin, kind, url) VALUES (?, ?, ?, ?, ?)", cls.values(task) )
        return task

    @classmethod
    def values(cls, task):
        return (task.id, task.status, task.origin, task.kind, task.url)

def check(db):
    db.deploypacket('web',1,"CREATE TABLE web_url_task (id INTEGER NOT NULL, status TEXT NOT NULL, origin INTEGER NULL, kind TEXT NOT NULL, url TEXT NOT NULL, PRIMARY KEY(id))")