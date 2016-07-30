import sqlite3

from consts import DB_NAME
from common import AttrDict
from schema import TABLE_SCHEMAS
from verbosity import verbose, set_verbosity


g_conn = None
g_table_info = AttrDict()  # {tname: TableColumns()}


class TableColumns(object):

    def __init__(self, *args, sep='|'):
        self._sep = sep
        self._cols = args

    def __repr__(self):
        return self._sep.join(self.cols)

    @property
    def sep(self):
        return self._sep

    @sep.setter
    def sep(self, value):
        self._sep = value

    @property
    def cols(self):
        return self._extract(1)

    def _extract(self, index):
        return (col[index] for col in self._cols)


def connect():
    global g_conn
    if g_conn is None:
        g_conn = sqlite3.connect(DB_NAME)
        verbose(2, 'connected to', DB_NAME)


def disconnect():
    global g_conn
    if g_conn is not None:
        g_conn.commit()
        g_conn.close()
        verbose(2, 'closed connection to:', DB_NAME)
        g_conn = None


def init(drop=False):
    connect()

    for tname in ['tasks']:
        if drop or not load_table_info(tname):
            _drop_create_table(tname)
            load_table_info(tname)


def load_table_info(tname):
    if tname not in g_table_info:
        cols = g_conn.cursor().execute('PRAGMA table_info("{}")'.format(tname)).fetchall()
        if cols:
            g_table_info[tname] = TableColumns(*cols)
            verbose(2, 'loaded info of table:', tname)

        else:
            return None

    return g_table_info[tname]


def _drop_create_table(tname):
    cur = g_conn.cursor()
    cur.execute('DROP TABLE IF EXISTS ' + tname)
    cur.execute('CREATE TABLE {} ({})'.format(tname, str(TABLE_SCHEMAS[tname])))
    verbose(1, 'initialized table:', tname)


def create_task(**kwargs):
    task = TABLE_SCHEMAS.tasks.new(**kwargs)
    sql = 'INSERT INTO tasks ({}) VALUES ({})'.format(*task.for_insert())
    g_conn.cursor().execute(sql)
    g_conn.commit()
    verbose(1, 'added task', repr(task))


def update_task(**kwargs):
    task = TABLE_SCHEMAS.tasks.new(**kwargs)
    sql = 'UPDATE tasks SET {} WHERE name="{}"'.format(task.for_update(), kwargs['name'])
    g_conn.cursor().execute(sql)
    g_conn.commit()
    verbose(1, 'updated task', repr(task))


def read_task(name):
    sql = 'SELECT * FROM tasks WHERE name="{}"'.format(name)
    values = g_conn.cursor().execute(sql).fetchone()
    if not values:
        raise NameError('missing task: ' + name)

    task = TABLE_SCHEMAS.tasks.new(**dict(zip(g_table_info.tasks.cols, values)))
    verbose(1, 'got task', repr(task))
    return task


def delete_task(name):
    read_task(name)

    sql = 'DELETE FROM tasks WHERE name="{}"'.format(name)
    g_conn.cursor().execute(sql)
    g_conn.commit()
    verbose(1, 'deleted task:', name)


def list_tasks(rowsep='\n', colsep='|'):
    sql = 'SELECT * FROM tasks'
    return rowsep.join(colsep.join(row) for row in g_conn.cursor().execute(sql).fetchall())


if __name__ == '__main__':
    set_verbosity(1)
    init(True)
    sep = '\n\t\t\t'
    verbose(1, 'info tasks:', str(g_table_info.tasks))
    create_task(name='task1', schedule='daily')
    verbose(1, 'all tasks:', '\t' + list_tasks(sep))
    create_task(name='task2', schedule='continuous')
    verbose(1, 'all tasks:', '\t' + list_tasks(sep))
    update_task(name='task2', state='running')
    verbose(1, 'got task', repr(read_task('task2')))
    delete_task(name='task1')
    verbose(1, 'all tasks:', '\t' + list_tasks(sep))
