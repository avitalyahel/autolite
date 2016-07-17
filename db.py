import sqlite3

from consts import DB_NAME
from common import AttrDict
from schema import TABLE_SCHEMAS
from verbosity import verbose, set_verbosity


g_conn = None


def connect():
    global g_conn
    if g_conn is None:
        g_conn = sqlite3.connect(DB_NAME)
        verbose(1, 'connected to', DB_NAME)


def disconnect():
    global g_conn
    if g_conn is not None:
        g_conn.close()
        verbose(1, 'closed connection to', DB_NAME)
        g_conn = None


def init():
    _init_table('tasks')


def _init_table(tname):
    cur = g_conn.cursor()
    cur.execute('DROP TABLE IF EXISTS ' + tname)
    cur.execute('CREATE TABLE {} ({})'.format(tname, str(TABLE_SCHEMAS[tname])))
    verbose(1, 'initialized table:', tname)


def add_task(**kwargs):
    task = TABLE_SCHEMAS.tasks.new(**kwargs)
    sql = 'INSERT INTO tasks ({}) VALUES ({})'.format(*task.for_insert())
    g_conn.cursor().execute(sql)
    verbose(1, 'added task', repr(task))


def update_task(**kwargs):
    task = TABLE_SCHEMAS.tasks.new(**kwargs)
    sql = 'UPDATE tasks SET {} WHERE name="{}"'.format(task.for_update(), kwargs['name'])
    g_conn.cursor().execute(sql)
    verbose(1, 'updated task:', repr(task))


if __name__ == '__main__':
    set_verbosity(1)
    connect()

    try:
        init()
        add_task(name='task1', schedule='daily')
        add_task(name='task2', schedule='continuous')
        update_task(name='task2', state='running')
        verbose(0, 'all tasks:', g_conn.cursor().execute('SELECT * FROM tasks').fetchall())

    finally:
        disconnect()
