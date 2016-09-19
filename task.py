from datetime import datetime

import db
from entity import Entity

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'


class Task(Entity):
    _tableName = 'tasks'

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

    def expired(self, timeout: int) -> bool:
        task_last_dt = datetime.strptime(self.last, DATETIME_FORMAT)
        return (datetime.now() - task_last_dt).total_seconds() > timeout

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
