import db
import schema


class MetaEntity(type):

    @property
    def tableName(self):
        return self._tableName


class Entity(metaclass=MetaEntity):
    _tableName = ''

    def __init__(self, name: str = '', schema: schema.TableSchema = None):
        assert bool(name) ^ bool(schema), 'may init with name XOR schema'

        if name:
            self._db_record = db.read(self._tableName, name=name)

        elif schema:
            self._db_record = schema

    def __repr__(self):
        return repr(self._db_record)

    def __getattr__(self, name):
        return self._db_record.__getattr__(name)

    @classmethod
    def create(cls, **kwargs) -> object:
        return cls(schema=db.create(cls.tableName, **kwargs))

    @classmethod
    def list(cls, **kwargs) -> tuple:
        return (cls(schema=db_record) for db_record in db.list_table(cls.tableName, **kwargs))

    @property
    def tableName(self):
        return type(self).tableName

    @property
    def __dict__(self):
        return self._db_record
