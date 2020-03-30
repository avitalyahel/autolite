import os
import sqlite3
from typing import Iterator

import settings
from common import AttrDict
from schema import TABLE_SCHEMAS, TableSchema
from verbosity import verbose, set_verbosity


g_conn = None
g_db_path = ''
g_table_columns = AttrDict()  # {tname: TableColumns()}


def name() -> str:
    return os.path.basename(g_db_path)


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
        global g_db_path
        g_db_path = os.path.expanduser(settings.read().db_path)
        g_conn = sqlite3.connect(g_db_path)
        verbose(2, 'connected to', g_db_path)


def disconnect():
    global g_conn

    if g_conn is not None:
        g_conn.commit()
        g_conn.close()
        verbose(2, 'closed connection to:', g_db_path)
        g_conn = None


def init(drop=False):
    connect()

    for tname in TABLE_SCHEMAS.keys():
        if drop or not load_table_info(tname):
            _drop_create_table(tname)
            load_table_info(tname)


def fini():
    for tname in TABLE_SCHEMAS.keys():
        if tname in g_table_columns:
            del g_table_columns[tname]

    disconnect()


def load_table_info(tname):
    if tname not in g_table_columns:
        cols = g_conn.cursor().execute('PRAGMA table_info("{}")'.format(tname)).fetchall()

        if cols:
            g_table_columns[tname] = TableColumns(*cols)
            verbose(2, 'loaded info of table:', tname)

        else:
            return None

    return g_table_columns[tname]


def _drop_create_table(tname):
    cur = g_conn.cursor()
    cur.execute('DROP TABLE IF EXISTS ' + tname)
    cur.execute('CREATE TABLE {} ({})'.format(tname, str(TABLE_SCHEMAS[tname])))
    verbose(2, 'initialized table:', tname)


def create(table, **kwargs):
    _assert_not_existing(table, kwargs['name'])

    record = TABLE_SCHEMAS[table].new(**kwargs)
    sql = 'INSERT INTO {} ({}) VALUES ({})'.format(table, *record.for_insert())
    g_conn.cursor().execute(sql)
    g_conn.commit()
    verbose(1, 'created', table[:-1], repr(record))
    return record


def update(table, **kwargs):
    _assert_existing(table, kwargs['name'])

    record = TABLE_SCHEMAS[table].new(**kwargs)
    sql = 'UPDATE {} SET {} WHERE name=\'{}\''.format(table, record.for_update(**kwargs), kwargs['name'])
    g_conn.cursor().execute(sql)
    g_conn.commit()
    verbose(2, 'updated', table[:-1], repr(record))


def read(table, name) -> TableSchema:
    sql = 'SELECT * FROM {} WHERE name=\'{}\''.format(table, name)
    verbose(2, 'reading:', sql)
    values = g_conn.cursor().execute(sql).fetchone()

    if not values:
        raise NameError('missing from {}: {}'.format(table, name))

    record = _new_schema(table, values)
    verbose(2, 'read', table[:-1], repr(record))
    return record


def existing(table, name) -> bool:
    sql = 'SELECT 1 FROM {} WHERE name=\'{}\' LIMIT 1'.format(table, name)
    values = g_conn.cursor().execute(sql).fetchone()
    exists = values is not None and len(values) > 0
    verbose(2, name, 'does' if exists else 'does not', 'exist')
    return exists


def _assert_existing(table, name):
    if not existing(table, name=name):
        raise NameError('missing from {}: {}'.format(table, name))


def _assert_not_existing(table, name):
    if existing(table, name=name):
        raise NameError('already exists in {}: {}'.format(table, name))


def delete(table, name):
    _assert_existing(table, name)

    sql = 'DELETE FROM {} WHERE name=\'{}\''.format(table, name)
    g_conn.cursor().execute(sql)
    g_conn.commit()
    verbose(1, 'deleted', table[:-1] + ':', name)


def list_table(table, **where) -> Iterator:
    return (_new_schema(table, row) for row in rows(table, **where))


def rows(table, sep='', **where) -> iter:
    sql = 'SELECT * FROM ' + table

    if where:
        sql += ' WHERE ' + TABLE_SCHEMAS[table].new(**where).for_where(**where)

    verbose(3, sql)
    return iter(sep.join(row) if sep else row
                for row in g_conn.cursor().execute(sql).fetchall())


def _new_schema(table, values) -> TableSchema:
    return TABLE_SCHEMAS[table].new(**dict(zip(g_table_columns[table].names, values)))


if __name__ == '__main__':
    set_verbosity(2)
    init(drop=True)
    sep = '\n\t\t\t'

    table = 'tasks'
    verbose(1, 'info tasks:', str(g_table_columns.tasks))
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

    table = 'systems'
    verbose(1, 'info systems:', str(g_table_columns.systems))
    create(table, name='sys1')
    assert existing(table, name='sys1')
    verbose(1, 'all systems:', '\t' + sep.join(rows('systems', sep='|')))
    create(table, name='sys2', installer='install.sh')
    verbose(1, 'all systems:', '\t' + sep.join(rows('systems', sep='|')))
    update(table, name='sys2', cleaner='clean.sh')
    verbose(1, 'got task', repr(read(table, 'sys2')))
    verbose(1, 'system list:\n', '\n'.join(repr(sys) for sys in list_table('systems')))
    delete(table, name='sys1')
    assert not existing(table, name='sys1')
    verbose(1, 'all systems:', '\t' + sep.join(rows('systems', sep='|')))
