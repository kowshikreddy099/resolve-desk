import json
import os
import sqlite3
import uuid
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from actions import resolve
from resolver import BASE, KB, analyze

DATABASE = os.environ.get('RESOLVE_DB', str(BASE / 'cases.sqlite'))
STATES = ('Open', 'In progress', 'Resolved')
TEAMS = [entry['team'] for entry in KB] + ['Manual review']

def connect():
    db = sqlite3.connect(DATABASE, timeout=8)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db

def initialize():
    with closing(connect()) as db:
        db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS cases(
          id TEXT PRIMARY KEY, fingerprint TEXT UNIQUE, text TEXT, team TEXT,
          priority TEXT, plan TEXT, status TEXT DEFAULT 'Open', version INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS demo_actions(reference TEXT PRIMARY KEY, kind TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS history(
          id INTEGER PRIMARY KEY, case_id TEXT REFERENCES cases(id),
          at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')), note TEXT);
        CREATE INDEX IF NOT EXISTS history_case ON history(case_id,id);
        """)

def field(data, key, low, high):
    value = data.get(key)
    if not isinstance(value, str) or not low <= len(value.strip()) <= high:
        raise ValueError(f'{key} must contain {low} to {high} characters.')
    return value.strip()

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, mime='application/json'):
        payload = json.dumps(body).encode() if mime == 'application/json' else body
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/health':
            return self.reply(200, {'service':'resolve-desk','api':2})
        if path in ('/', '/app.js'):
            file = 'index.html' if path == '/' else 'app.js'
            return self.reply(200, (BASE/'static'/file).read_bytes(), 'text/html; charset=utf-8' if path=='/' else 'text/javascript; charset=utf-8')
        with closing(connect()) as db:
            if path == '/api/cases':
                return self.reply(200, [dict(row) for row in db.execute('SELECT id,text,team,priority,status,version,plan FROM cases ORDER BY rowid DESC')])
            if path.startswith('/api/history/'):
                return self.reply(200,[dict(row) for row in db.execute('SELECT at,note FROM history WHERE case_id=? ORDER BY id',(path.split('/')[-1],))])
        self.reply(404, {'error':'Unknown endpoint'})

    def do_POST(self):
        if self.headers.get('Origin') not in (None,'http://'+self.headers.get('Host','')):
            return self.reply(403, {'error':'Origin mismatch'})
        if self.headers.get_content_type() != 'application/json':
            return self.reply(415, {'error':'JSON required'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 32768:
                return self.reply(413, {'error':'Invalid body size'})
            data = json.loads(self.rfile.read(length))
            if not isinstance(data,dict):
                raise ValueError('Expected an object')
            with closing(connect()) as db, db:
                status, result = self.action(db, data)
            self.reply(status, result)
        except (ValueError, UnicodeError) as exc:
            self.reply(400, {'error': str(exc)})
        except sqlite3.OperationalError:
            self.reply(503, {'error':'Database unavailable. Retry shortly.'})

    def action(self, db, data):
        if self.path in ('/api/analyze','/api/cases','/api/resolve'):
            text = field(data,'text',10,3000)
            result = analyze(text)
            if self.path == '/api/analyze':
                return 200,result
            key = ' '.join(text.casefold().split())
            cid = str(uuid.uuid4())
            inserted = db.execute('INSERT INTO cases(id,fingerprint,text,team,priority,plan) VALUES(?,?,?,?,?,?) ON CONFLICT(fingerprint) DO NOTHING',
                (cid,key,text,result['team'],result['priority'],result['plan'])).rowcount
            if inserted:
                db.execute('INSERT INTO history(case_id,note) VALUES(?,?)',(cid,'Case opened'))
            row = db.execute('SELECT * FROM cases WHERE fingerprint=?',(key,)).fetchone()
            if self.path == '/api/resolve' and row['status'] != 'Resolved':
                prior = db.execute("SELECT 1 FROM history WHERE case_id=? AND instr(note,'Automatic response: ')>0",(row['id'],)).fetchone()
                if not prior:
                    resolve(db,row)
            result = {'id':row['id']}
            if self.path == '/api/resolve':
                result['record'] = dict(db.execute('SELECT id,text,team,priority,status,version,plan FROM cases WHERE id=?',(row['id'],)).fetchone())
                result['history'] = [dict(event) for event in db.execute('SELECT at,note FROM history WHERE case_id=? ORDER BY id',(row['id'],))]
            return (201 if inserted else 200),result
        if self.path.startswith('/api/update/'):
            cid = self.path.split('/')[-1]
            note = field(data,'note',1,500)
            state,team = data.get('status'),data.get('team')
            if state not in STATES or team not in TEAMS or type(data.get('version')) is not int:
                raise ValueError('Invalid update')
            changed = db.execute('UPDATE cases SET status=?,team=?,version=version+1 WHERE id=? AND version=?',(state,team,cid,data['version'])).rowcount
            if not changed:
                return 409,{'error':'Case changed. Reopen it to load the latest update.'}
            db.execute('INSERT INTO history(case_id,note) VALUES(?,?)',(cid,f'{state} | {team} | {note}'))
            return 200,{'id':cid}
        return 404,{'error':'Unknown endpoint'}

if __name__ == '__main__':
    initialize()
    port = int(os.environ.get('RESOLVE_PORT','8451'))
    print(f'Resolve Desk running at http://127.0.0.1:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()

