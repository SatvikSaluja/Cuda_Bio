"""Local SQLite persistence. Sequence payloads are fetched only on demand."""
from contextlib import contextmanager
from pathlib import Path
import json
import sqlite3
import time

SORTS={'query_id':'query_id','score':'score','edit_distance':'edit_distance','execution_time':'execution_time'}
class Store:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,status TEXT NOT NULL,completed INTEGER DEFAULT 0,
                    created REAL NOT NULL,updated REAL NOT NULL,options TEXT NOT NULL,error TEXT);
                CREATE TABLE IF NOT EXISTS results(job TEXT NOT NULL,idx INTEGER NOT NULL,query_id TEXT NOT NULL,
                    score INTEGER,edit_distance INTEGER,execution_time REAL,metadata TEXT NOT NULL,detail TEXT NOT NULL,
                    PRIMARY KEY(job,idx),FOREIGN KEY(job) REFERENCES jobs(id) ON DELETE CASCADE);
                CREATE INDEX IF NOT EXISTS results_query ON results(job,query_id);
                CREATE TABLE IF NOT EXISTS measurements(id INTEGER PRIMARY KEY,created REAL NOT NULL,body TEXT NOT NULL);
            ''')
        self.path.chmod(0o600)
    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=30)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:yield db
        finally:db.close()
    def create(self,id,options):
        with self.connect() as db:
            if db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]>=4:
                raise ValueError('Local job queue is full')
            db.execute('INSERT INTO jobs VALUES(?,?,0,?,?,?,NULL)',(id,'queued',time.time(),time.time(),json.dumps(options)))
    def update(self,id,status,error=None):
        with self.connect() as db:
            db.execute('UPDATE jobs SET status=?,error=?,updated=? WHERE id=?',(status,error,time.time(),id))
    def job(self,id):
        with self.connect() as db:r=db.execute('SELECT * FROM jobs WHERE id=?',(id,)).fetchone()
        if r is None:raise KeyError(id)
        d=dict(r);d['options']=json.loads(d['options']);return d
    def jobs(self):
        with self.connect() as db:rows=db.execute('SELECT * FROM jobs ORDER BY created DESC').fetchall()
        results=[]
        for row in rows:
            item=dict(row);item['options']=json.loads(item['options']);results.append(item)
        return results
    def append(self,id,row):
        meta={k:v for k,v in row.items() if k not in ('query_sequence','target_sequence')}
        with self.connect() as db:
            state=db.execute('SELECT completed,status FROM jobs WHERE id=?',(id,)).fetchone()
            if state is None or state['status']!='running':raise RuntimeError('Job cancelled')
            idx=state['completed'];meta['result_index']=idx
            db.execute('INSERT INTO results VALUES(?,?,?,?,?,?,?,?)',(id,idx,row['query_id'],row['score'],row['edit_distance'],row['execution_time'],json.dumps(meta),json.dumps(row)))
            db.execute('UPDATE jobs SET completed=completed+1,updated=? WHERE id=?',(time.time(),id))
    def results(self,id,offset=0,limit=200,search='',sort='query_id',descending=False):
        if sort not in SORTS:raise ValueError('Invalid sort field')
        query='FROM results WHERE job=? AND instr(lower(query_id),lower(?))>0'
        with self.connect() as db:
            total=db.execute('SELECT count(*) '+query,(id,search)).fetchone()[0]
            rows=db.execute('SELECT metadata '+query+' ORDER BY '+SORTS[sort]+(' DESC' if descending else ' ASC')+',idx LIMIT ? OFFSET ?',(id,search,limit,offset)).fetchall()
        return total,[json.loads(r[0]) for r in rows]
    def detail(self,id,index):
        with self.connect() as db:r=db.execute('SELECT detail FROM results WHERE job=? AND idx=?',(id,index)).fetchone()
        if r is None:raise KeyError(index)
        return json.loads(r[0])
    def export(self,id):
        # Read a bounded page at a time; do not hold a DB lock while streaming.
        offset=0
        while True:
            with self.connect() as db:rows=db.execute('SELECT detail FROM results WHERE job=? ORDER BY idx LIMIT 100 OFFSET ?',(id,offset)).fetchall()
            if not rows:return
            for row in rows:yield json.loads(row[0])
            offset+=len(rows)
    def clear(self):
        with self.connect() as db:db.execute("DELETE FROM jobs WHERE status NOT IN ('running','queued')")
    def recover(self):
        with self.connect() as db:db.execute("UPDATE jobs SET status='interrupted',error='Service stopped before completion' WHERE status IN ('running','queued')")
    def measurement(self,row):
        with self.connect() as db:
            db.execute('INSERT INTO measurements(created,body) VALUES(?,?)',(time.time(),json.dumps(row)))
            db.execute('DELETE FROM measurements WHERE id NOT IN (SELECT id FROM measurements ORDER BY id DESC LIMIT 1000)')
    def measurements(self):
        with self.connect() as db:return [json.loads(r[0]) for r in db.execute('SELECT body FROM measurements ORDER BY id')]
