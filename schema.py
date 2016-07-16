from types import AttrDict


class TableSchema(AttrDict):

    def __str__(self):
        return ','.join(' '.join(kv) for kv in self.items())

    def __repr__(self):
        return ', '.join(': '.join([k, v]) for k, v in self.items() if v)

    def new(self, **kwargs):
        result = TableSchema((k, PYTYPES[v]()) for k, v in self.items())
        result.update(dict((k, v) for k, v in kwargs.items() if k in result))
        return result

    def for_insert(self):
        cols, vals = zip(*[(k, _quoted(v)) for k, v in self.items() if v])
        return ','.join(cols), ','.join(vals)


def _quoted(val):
    if isinstance(val, str):
        return '"{}"'.format(val)

    else:
        return str(val)


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
        schedule='TEXT',
        last='TEXT',
        state='TEXT',
    ),
)
