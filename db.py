import sqlite3

from consts import DB_NAME
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
    cur.execute('CREATE TABLE {} ({})'.format(tname, repr(TABLE_SCHEMAS[tname])))
    verbose(1, 'initialized table', tname)


if __name__ == '__main__':
    set_verbosity(1)
    connect()
    init()
    disconnect()
