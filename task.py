import yaml
from datetime import datetime
from contextlib import contextmanager

import db
import mail
import settings
from entity import Entity
from common import AttrDict
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
        del cls._walkParents[-1]

    @property
    def mailClient(self):
        if not hasattr(self, '_mailClient'):
            email_settings = settings.read().email
            self._mailClient = mail.Email(
                smtp_server=email_settings.server,
                smtp_port=email_settings.port,
                smtp_username=email_settings.username,
                smtp_password=email_settings.password,
            )

        return self._mailClient

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
    def lastDT(self) -> datetime:
        return datetime.strptime(self._db_record.last, DATETIME_FORMAT)

    def expired(self, timeout: int) -> bool:
        return (datetime.now() - self.lastDT).total_seconds() > timeout

    def start(self):
        with self.notifyStateChangeContext():
            self._db_record.state = 'running'
            self._db_record.last = datetime.now()
            db.update('tasks', name=self.name, state=self._db_record.state, last=self._db_record.last)

    def fail(self):
        with self.notifyStateChangeContext():
            self._db_record.state = 'failed'
            db.update('tasks', name=self.name, state=self._db_record.state)

    def reset(self):
        with self.notifyStateChangeContext():
            self._db_record.state = 'pending'
            db.update('tasks', name=self.name, state=self._db_record.state)

    @contextmanager
    def notifyStateChangeContext(self):
        state = self.state

        yield

        self.notify('task {} now {} (was {})'.format(self.name, self.state, state)
                    if self.state != state else '')

    def notify(self, subject: str = ''):
        if self.email:
            _subject = subject if subject else 'task {name} now {state}'.format(self.name, self.state)

            self.mailClient.send(
                recipients=self.email.split(','),
                subject='autolite: ' + _subject,
                content=yaml.dump(self.__dict__, default_flow_style=False).replace('\n', '<br/>'),
            )

    def delete(self):
        db.delete('tasks', name=self.name)
        self._db_record = None


if __name__ == '__main__':
    db.init()
    for t, l in Task.walkIter(parent=''):
        print('\t' * l, str(t))
    db.fini()
