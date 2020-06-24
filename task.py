import os
from contextlib import contextmanager
from datetime import datetime, timedelta

import yaml

import db
import mail
import settings
from entity import Entity
from verbosity import verbose

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'


class Task(Entity):
    _tableName = 'tasks'

    _walkParents = []

    @classmethod
    def walkIter(cls, **kwargs):  # yield task, level
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

    def inheritedAttr(self, attr: str) -> object:
        db_record = self._db_record

        while getattr(db_record, attr) == '<inherit>':
            assert db_record.parent, 'missing parent for <inherit>'
            db_record = db.read('tasks', db_record.parent)

        return getattr(db_record, attr)

    @property
    def mailClient(self) -> mail.Email:
        if not hasattr(self, '_mailClient'):
            email_settings = settings.read().email

            if any(not value for value in email_settings.values()):
                self._mailClient = mail.FakeEmail()

            else:
                try:
                    self._mailClient = mail.Email(
                        smtp_server=email_settings.server,
                        smtp_port=email_settings.port,
                        smtp_username=email_settings.username,
                        smtp_password=email_settings.password,
                    )

                except Exception as exc:
                    verbose(0, 'Warning! mail client returned with error:', str(exc),
                            email_settings,
                            type(email_settings.server),
                            type(email_settings.port),
                            type(email_settings.username),
                            type(email_settings.password),
                            '\nNotifying to stdout.')
                    self._mailClient = mail.FakeEmail()

        return self._mailClient

    @property
    def continuous(self) -> bool:
        return self.inheritedAttr('schedule') == 'continuous'

    @property
    def daily(self) -> bool:
        return self.inheritedAttr('schedule') == 'daily'

    @property
    def hourly(self) -> bool:
        return self.inheritedAttr('schedule') == 'hourly'

    @property
    def never(self) -> bool:
        return self.inheritedAttr('schedule') == 'never'

    @property
    def once(self) -> bool:
        return self._db_record.last.find('<once>') > -1

    @property
    def ready(self) -> bool:
        if not self.pending:
            return False

        if self.continuous:
            return True

        if self.hourly:
            now = datetime.now()
            now_modulu_hour = now - timedelta(minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
            return str(now_modulu_hour) > self._db_record.last

        if self.daily:
            return str(datetime.now().date()) > self._db_record.last

    @property
    def condition(self) -> bool:
        condition = self.inheritedAttr('condition')
        result = not condition or not os.system('export AUTOLITE_TASK_NAME="{}" ; '.format(self.name) + str(condition))
        verbose(2, 'condition:', condition, 'result:', result)
        return result

    @property
    def pending(self) -> bool:
        return self._db_record.state == 'pending'

    @property
    def failed(self) -> bool:
        return self._db_record.state == 'failed'

    @property
    def running(self) -> bool:
        return self._db_record.state == 'running'

    @property
    def lastDT(self) -> datetime:
        return datetime.strptime(self._db_record.last, DATETIME_FORMAT)

    def expired(self, timeout: int) -> bool:
        return (datetime.now() - self.lastDT).total_seconds() > timeout

    def holdingAny(self, resources: str) -> bool:
        return bool(self.resources and resources and (set(self.resources.split(' ')) & set(resources.split(' '))))

    def start(self, log: str = ''):
        with self.notifyStateChangeContext():
            self._setLast(str(datetime.now()))
            self._db_record.state = 'running'
            self._db_record.log = log
            db.update('tasks', name=self.name, state=self._db_record.state, last=self._db_record.last,
                      log=self._db_record.log)

    def fail(self):
        with self.notifyStateChangeContext():
            self._db_record.state = 'failed'
            db.update('tasks', name=self.name, state=self._db_record.state)

    def reset(self):
        with self.notifyStateChangeContext():
            self._db_record.state = 'pending'
            db.update('tasks', name=self.name, state=self._db_record.state, last=self._db_record.last)

    def skip(self):
        with self.notifyStateChangeContext():
            self._setLast('')
            self._db_record.state = 'pending'
            db.update('tasks', name=self.name, state=self._db_record.state, last=self._db_record.last)

    def updateLast(self, last: str):
        self._setLast(last)
        db.update('tasks', name=self.name, last=self._db_record.last)

    def _setLast(self, last: str):
        self._db_record.last = last + ('<once>' if self.once else '')

    @contextmanager
    def notifyStateChangeContext(self):
        state = self.state

        yield

        if self.pending and state == 'running':
            self.notify('task {} succeeded'.format(self.name))

        else:
            self.notify('task {} {} (was {})'.format(self.name, self.state, state)
                        if self.state != state else '')

    def notify(self, subject: str = ''):
        if self.email:
            _subject = subject if subject else 'task {} {}'.format(self.name, self.state)

            self.mailClient.send(
                recipients=self.email.split(','),
                subject='autolite: ' + _subject,
                content=yaml.dump(self.__dict__, default_flow_style=False),
            )

    def delete(self):
        db.delete('tasks', name=self.name)
        self._db_record = None


if __name__ == '__main__':
    db.init()
    for t, l in Task.walkIter(parent=''):
        print('\t' * l, str(t))
    db.fini()
