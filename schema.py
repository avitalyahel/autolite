from common import AttrDict


class TableSchema(AttrDict):

    def __str__(self):
        return ','.join(' '.join(kv) for kv in self.items())

    def __repr__(self):
        return 'name: {}, {}'.format(
            self.name, ', '.join(': '.join([k, v]) for k, v in self.items() if k != 'name' and v)
        )

    def new(self, **kwargs):
        result = TableSchema((k, PYTYPES[v]()) for k, v in self.items())
        result.update(dict((k, _empty(v)) for k, v in kwargs.items() if k in result))
        return result

    def for_insert(self):
        cols, vals = zip(*[(k, _quoted(v)) for k, v in self.items()])
        return ','.join(cols), ','.join(vals)

    def for_update(self, **kwargs):
        return ','.join('='.join([k, _quoted(v)]) for k, v in self.items() if v or k in kwargs)

    def for_where(self, **kwargs):
        return ' AND '.join('{}={}'.format(k, _quoted(v)) for k, v in self.items() if v or k in kwargs)


def _quoted(val):
    return '"{}"'.format(val) if isinstance(val, str) else _empty(val)


def _empty(val):
    return '' if val is None else str(val)


PYTYPES = dict(
    INTEGER=int,
    TEXT=str,
    REAL=float,
    BLOB=bytes,
    NULL=type(None),
)


TABLE_SCHEMAS = AttrDict(
    tasks=TableSchema(
        name='TEXT',
        parent='TEXT',
        schedule='TEXT',
        state='TEXT',
        condition='TEXT',
        command='TEXT',
        email='TEXT',
        last='TEXT',
    ),
    systems=TableSchema(
        name='TEXT',
        ip='TEXT',
        installer='TEXT',
        cleaner='TEXT',
        monitor='TEXT',
        config='TEXT',
        user='TEXT',
        comment='TEXT',
    ),
)

SCHEDULES = ['daily', 'hourly', 'continuous', 'never']
