import dbmeta

class Task:
    def __init__(self):
        dbmeta.DbMeta.init(Task, self)

    @classmethod
    def get(cls, db, id):
        return dbmeta.DbMeta.get(db, cls, id)

class UrlTask:
    def __init__(self):
        dbmeta.DbMeta.init(UrlTask, self)

    @classmethod
    def create(cls, db, url):
        task = cls()
        task.id = db.genid()
        task.status = 'init'
        task.origin = None
        task.kind = 'document'
        task.url = url
        return dbmeta.DbMeta.insert(db, cls, task)

    @classmethod
    def get(cls, db, id):
        return dbmeta.DbMeta.get(db, cls, id)

class Loading:
    def __init__(self):
        dbmeta.DbMeta.init(Loading, self)

    @classmethod
    def create(cls, db, task, request, responce)

def init(db):
    db.deploypacket('web',1,
        [ "CREATE TABLE web_url_task (id INTEGER NOT NULL, status TEXT NOT NULL, origin INTEGER NULL, kind TEXT NOT NULL, url TEXT NOT NULL, PRIMARY KEY(id))",
          "CREATE VIEW web_tasks (id, kind, status) AS SELECT id, 'url', status FROM web_url_task",
          "CREATE TABLE web_loading (id INTEGET NOT NULL, urltask INTEGER NOT NULL, request BLOB NOT NULL, responce BLOB NULL, PRIMARY KEY(id), FOREIGN KEY (url_task) REFERENCES web_url_task (id))" ] )
    dbmeta.DbMeta.set(Task, 'web_tasks', ['id', 'kind', 'status'])
    dbmeta.DbMeta.set(UrlTask, 'web_url_task', ['id', 'status', 'origin', 'kind', 'url'])
    dbmeta.DbMeta.set(Loading, 'web_loading', ['id', 'urltask', 'request', 'responce'])
