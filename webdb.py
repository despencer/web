
def check(db):
    db.deploypacket('web',1,"CREATE TABLE web_url_task (id INTEGER NOT NULL, url TEXT NOT NULL, status TEXT NOT NULL, PRIMARY KEY(id))")