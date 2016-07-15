from types import AttrDict


class TableSchema(AttrDict):

    def __repr__(self):
        return ', '.join(' '.join(kv) for kv in self.items())


TABLE_SCHEMAS = AttrDict(
    tasks=TableSchema(
        name='TEXT',
        schedule='TEXT',
        last='TEXT',
        state='TEXT',
    ),
)
