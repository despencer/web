import dbmeta

class Task:
    def __init__(self):
        dbmeta.DbMeta.init(Task, self, ['id', 'kind', 'status'])

    @classmethod
    def get(cls, db, id):
        res = db.execute("SELECT id, kind, status FROM web_tasks WHERE id = ?", (id, ))
        if(len(res) == 0):
            return None
        return dbmeta.DbMeta.fromvalues(Task, res[0])

class UrlTask:
    def __init__(self):
        dbmeta.DbMeta.init(UrlTask, self, ['id', 'status', 'origin', 'kind', 'url'])

    @classmethod
    def create(cls, db, url):
        task = cls()
        task.id = db.genid()
        task.status = 'init'
        task.origin = None
        task.kind = 'document'
        task.url = url
        db.execute("INSERT INTO web_url_task (id, status, origin, kind, url) VALUES (?, ?, ?, ?, ?)", dbmeta.DbMeta.values(cls, task) )
        return task

    @classmethod
    def get(cls, db, id):
        res = db.execute("SELECT id, status, origin, kind, url FROM web_url_task WHERE id = ?", (id, ))
        if(len(res) == 0):
            return None
        return dbmeta.DbMeta.fromvalues(UrlTask, res[0])

def check(db):
    db.deploypacket('web',1,
        [ "CREATE TABLE web_url_task (id INTEGER NOT NULL, status TEXT NOT NULL, origin INTEGER NULL, kind TEXT NOT NULL, url TEXT NOT NULL, PRIMARY KEY(id))",
          "CREATE VIEW web_tasks (id, kind, status) AS SELECT id, 'url', status FROM web_url_task" ] )
