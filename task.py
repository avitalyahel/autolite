from datetime import datetime
from contextlib import contextmanager

import db
from entity import Entity
from verbosity import verbose

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'


class Task(Entity):
    _tableName = 'tasks'

    _walkParents = []

    @classmethod
    def walkIter(cls, **kwargs):    # yield task, level
        for task in cls.list(**kwargs):
            if task.name in cls._walkParents:
                verbose(2, task.name, 'already in parents', cls._walkParents, ', skipping.')
                continue

            yield task, len(cls._walkParents)

            _kwargs = dict((k, v) for k, v in kwargs.items() if k not in ['name', 'parent'])

            with cls.walkParentsContext(parent=task.name):
                for subtask in cls.walkIter(parent=task.name, **_kwargs):
                    yield subtask

    @classmethod
    @contextmanager
    def walkParentsContext(cls, parent: str):
        cls._walkParents.append(parent)
        yield
        cls._walkParents.remove(parent)

    @property
    def continuous(self) -> bool:
        return self._db_record.schedule == 'continuous'

    @property
    def daily(self) -> bool:
        return self._db_record.schedule == 'daily'

    @property
    def never(self) -> bool:
        return self._db_record.schedule == 'never'

    @property
    def ready(self) -> bool:
        return self.continuous or self.daily and str(datetime.now().date()) > self._db_record.last

    @property
    def pending(self) -> bool:
        return self._db_record.state == 'pending'

    @property
    def failed(self) -> bool:
        return self._db_record.state == 'failed'

    @property
    def last(self) -> datetime:
        return datetime.strptime(self._db_record.last, DATETIME_FORMAT)

    def expired(self, timeout: int) -> bool:
        return (datetime.now() - self.last).total_seconds() > timeout

    def start(self):
        self._db_record.state = 'running'
        self._db_record.last = datetime.now()
        db.update('tasks', name=self.name, state=self._db_record.state, last=self._db_record.last)

    def fail(self):
        self._db_record.state = 'failed'
        db.update('tasks', name=self.name, state=self._db_record.state)

    def reset(self):
        self._db_record.state = 'pending'
        db.update('tasks', name=self.name, state=self._db_record.state)

    def delete(self):
        db.delete('tasks', name=self.name)
        self._db_record = None


if __name__ == '__main__':
    db.init()
    for t, l in Task.walkIter(parent=''):
        print('\t' * l, str(t))
    db.fini()
