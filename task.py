from datetime import datetime

import db
import schema

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'


class Task():

    def __init__(self, *args):
        self._db_task = None

        if not args:
            return

        assert len(args) == 1, 'may init with one arg only (passed: {})'.format(repr(args))

        arg = args[0]
        if isinstance(arg, str):
            self._db_task = db.read('tasks', name=arg)

        elif isinstance(arg, schema.TableSchema):
            self._db_task = arg

        else:
            raise TypeError('unexpected arg type ' + str(type(arg)))

    def __repr__(self):
        return repr(self._db_task)

    def __getattr__(self, name):
        return self._db_task[name]

    @classmethod
    def create(cls, **kwargs) -> object:
        return cls(db.create('tasks', **kwargs))

    @classmethod
    def list(cls, **kwargs) -> tuple:
        return (cls(db_task) for db_task in db.list_table('tasks', **kwargs))

    @property
    def continuous(self) -> bool:
        return self._db_task.schedule == 'continuous'

    @property
    def daily(self) -> bool:
        return self._db_task.schedule == 'daily'

    @property
    def never(self) -> bool:
        return self._db_task.schedule == 'never'

    @property
    def ready(self) -> bool:
        return self.continuous or self.daily and str(datetime.now().date()) > self._db_task.last

    @property
    def pending(self) -> bool:
        return self._db_task.state == 'pending'

    @property
    def failed(self) -> bool:
        return self._db_task.state == 'failed'

    def expired(self, timeout: int) -> bool:
        task_last_dt = datetime.strptime(self.last, DATETIME_FORMAT)
        return (datetime.now() - task_last_dt).total_seconds() > timeout

    def start(self):
        self._db_task.state = 'running'
        self._db_task.last = datetime.now()
        db.update('tasks', name=self.name, state=self._db_task.state, last=self._db_task.last)

    def fail(self):
        self._db_task.state = 'failed'
        db.update('tasks', name=self.name, state=self._db_task.state)

    def reset(self):
        self._db_task.state = 'pending'
        db.update('tasks', name=self.name, state=self._db_task.state)

    def delete(self):
        db.delete('tasks', name=self.name)
        self._db_task = None
