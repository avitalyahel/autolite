import sqlite3

from consts import DB_NAME
from common import AttrDict
from schema import TABLE_SCHEMAS, TableSchema
from verbosity import verbose, set_verbosity


g_conn = None
g_table_info = AttrDict()  # {tname: TableColumns()}


class TableColumns(object):

    def __init__(self, *args, sep='|'):
        self._sep = sep
        self._cols = args

    def __repr__(self):
        return self._sep.join(self.names)

    @property
    def sep(self):
        return self._sep

    @sep.setter
    def sep(self, value):
        self._sep = value

    @property
    def names(self):
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

    for tname in TABLE_SCHEMAS.keys():
        if drop or not load_table_info(tname):
            _drop_create_table(tname)
            load_table_info(tname)


def fini():
    for tname in TABLE_SCHEMAS.keys():
        if tname in g_table_info:
            del g_table_info[tname]

    disconnect()


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
    verbose(2, 'initialized table:', tname)


def create(table, **kwargs):
    record = TABLE_SCHEMAS[table].new(**kwargs)
    sql = 'INSERT INTO {} ({}) VALUES ({})'.format(table, *record.for_insert())
    g_conn.cursor().execute(sql)
    g_conn.commit()
    verbose(1, 'created', table[:-1], repr(record))
    return record


def update(table, **kwargs):
    _assert_existing(table, kwargs['name'])

    record = TABLE_SCHEMAS[table].new(**kwargs)
    sql = 'UPDATE tasks SET {} WHERE name="{}"'.format(record.for_update(), kwargs['name'])
    g_conn.cursor().execute(sql)
    g_conn.commit()
    verbose(2, 'updated', table[:-1], repr(record))


def read(table, name) -> TableSchema:
    sql = 'SELECT * FROM {} WHERE name="{}"'.format(table, name)
    values = g_conn.cursor().execute(sql).fetchone()

    if not values:
        raise NameError('missing {}: {}'.format(table, name))

    record = _new(table, values)
    verbose(1, 'read', table[:-1], repr(record))
    return record


def existing(table, name) -> bool:
    sql = 'SELECT 1 FROM {} WHERE name="{}" LIMIT 1'.format(table, name)
    values = g_conn.cursor().execute(sql).fetchone()
    return values is not None and len(values) > 0


def _assert_existing(table, name):
    if not existing(table, name=name):
        raise NameError('missing {}: {}'.format(table, name))


def delete(table, name):
    _assert_existing(table, name)

    sql = 'DELETE FROM {} WHERE name="{}"'.format(table, name)
    g_conn.cursor().execute(sql)
    g_conn.commit()
    verbose(1, 'deleted', table[:-1] + ':', name)


def list_table(table, **where):
    return (_new(table, row) for row in rows(table, **where))


def rows(table, sep='', **where):
    sql = 'SELECT * FROM ' + table

    if where:
        sql += ' WHERE ' + TABLE_SCHEMAS[table].new(**where).for_where()

    verbose(3, sql)
    return iter(sep.join(row) if sep else row
                for row in g_conn.cursor().execute(sql).fetchall())


def _new(table, values) -> TableSchema:
    return TABLE_SCHEMAS[table].new(**dict(zip(g_table_info[table].names, values)))


if __name__ == '__main__':
    set_verbosity(1)
    init(drop=True)
    sep = '\n\t\t\t'
    table = 'tasks'
    verbose(1, 'info tasks:', str(g_table_info.tasks))
    create(table, name='task1', schedule='daily')
    assert existing(table, name='task1')
    verbose(1, 'existing task1')
    verbose(1, 'all tasks:', '\t' + sep.join(rows('tasks', sep='|')))
    create(table, name='task2', schedule='continuous')
    verbose(1, 'all tasks:', '\t' + sep.join(rows('tasks', sep='|')))
    update(table, name='task2', state='running')
    verbose(1, 'got task', repr(read(table, 'task2')))
    verbose(1, 'task list:\n', '\n'.join(repr(task) for task in list_table('tasks')))
    delete(table, name='task1')
    assert not existing(table, name='task1')
    verbose(1, 'not existing task1')
    verbose(1, 'all tasks:', '\t' + sep.join(rows('tasks', sep='|')))
