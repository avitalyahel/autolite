import db
import schema


class MetaEntity(type):

    @property
    def tableName(self):
        return self._tableName


class Entity(metaclass=MetaEntity):
    _tableName = ''

    def __init__(self, *args):
        self._db_record = None

        if not args:
            return

        assert len(args) == 1, 'may init with one arg only (passed: {})'.format(repr(args))
        arg = args[0]

        if isinstance(arg, str):
            self._db_record = db.read(self._tableName, name=arg)

        elif isinstance(arg, schema.TableSchema):
            self._db_record = arg

        else:
            raise TypeError('unexpected arg type ' + str(type(arg)))

    def __repr__(self):
        return repr(self._db_record)

    def __getattr__(self, name):
        return self._db_record[name]

    @classmethod
    def create(cls, **kwargs) -> object:
        return cls(db.create(cls.tableName, **kwargs))

    @classmethod
    def list(cls, **kwargs) -> tuple:
        return (cls(db_task) for db_task in db.list_table(cls.tableName, **kwargs))
