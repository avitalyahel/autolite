import db
import schema


class MetaEntity(type):

    @property
    def tableName(self):
        return self._tableName


class Entity(metaclass=MetaEntity):
    _tableName = ''

    def __init__(self, name: str = '', record: schema.TableSchema = None):
        assert bool(name) ^ bool(record), 'may init with name XOR record'

        if name:
            self._db_record = db.read(self._tableName, name=name)

        elif record:
            self._db_record = record

        assert isinstance(self._db_record, schema.TableSchema)

    def __repr__(self):
        inherited = dict((k, self.inheritedAttr(k)) for k in self._db_record.keys())
        return repr(schema.TableSchema(**inherited))

    def __getattr__(self, name):
        try:
            return self.inheritedAttr(name)

        except KeyError:
            return self.__getattribute__(name)

    @property
    def __dict__(self):
        return dict(self._db_record)

    @classmethod
    def create(cls, **kwargs) -> object:
        return cls(record=db.create(cls.tableName, **kwargs))

    @classmethod
    def list(cls, **kwargs) -> tuple:
        return (cls(record=db_record) for db_record in db.list_table(cls.tableName, **kwargs))

    @property
    def tableName(self):
        return type(self).tableName

    def inheritedAttr(self, attr: str) -> object:
        return getattr(self._db_record, attr)

    def reload(self):
        self._db_record = db.read(self._tableName, name=self._db_record.name)
