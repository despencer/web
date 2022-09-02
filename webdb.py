class Task:
    def __init__(self):
        self.id = None
        self.kind = None
        self.status = None

    @classmethod
    def get(cls, db, id):
        res = db.execute("SELECT id, kind, status FROM web_tasks WHERE id = ?", (id, ))
        if(len(res) == 0):
            return None
        return cls.fromvalues(res[0])

    @classmethod
    def fromvalues(cls, values):
        task = cls()
        task.id = values[0]
        task.kind = values[1]
        task.status = values[2]
        return task

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
    def get(cls, db, id):
        res = db.execute("SELECT id, status, origin, kind, url FROM web_url_task WHERE id = ?", (id, ))
        if(len(res) == 0):
            return None
        return cls.fromvalues(res[0])

    @classmethod
    def values(cls, task):
        return (task.id, task.status, task.origin, task.kind, task.url)

    @classmethod
    def fromvalues(cls, values):
        task = cls()
        task.id = values[0]
        task.status = values[1]
        task.origin = values[2]
        task.kind = values[3]
        task.url = values[4]
        return task

def check(db):
    db.deploypacket('web',1,
        [ "CREATE TABLE web_url_task (id INTEGER NOT NULL, status TEXT NOT NULL, origin INTEGER NULL, kind TEXT NOT NULL, url TEXT NOT NULL, PRIMARY KEY(id))",
          "CREATE VIEW web_tasks (id, kind, status) AS SELECT id, 'url', status FROM web_url_task" ] )
