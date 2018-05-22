import os

import db
from entity import Entity
from common import active_user_name


class System(Entity):
    _tableName = 'systems'

    def acquire(self):
        if not self._db_record.user:
            self._db_record.user = active_user_name()
            db.update(self.tableName, name=self.name, user=self._db_record.user)

        elif self._db_record.user == active_user_name():
            raise UserWarning('you have already acquired: ' + self.name)

        else:
            raise PermissionError('already owned by: ' + self._db_record.user)

    def claim(self):
        if self._db_record.user and self._db_record.user != active_user_name():
            raise PermissionError('owned by other: {}'.format(self._db_record.user))

    def release(self, force: bool = False):
        if not self._db_record.user:
            raise UserWarning('already free: ' + self.name)

        elif self._db_record.user != active_user_name() and not force:
            raise PermissionError('owned by other: {}'.format(self._db_record.user))

        else:
            self._db_record.user = ''
            db.update(self.tableName, name=self.name, user=self._db_record.user)

    def install(self):
        self.claim()
        assert not os.system(self._db_record.installer)

    def clean(self):
        self.claim()
        assert not os.system(self._db_record.cleaner)

    def monitor(self):
        self.claim()
        return not os.system(self._db_record.monitor)

    def config(self):
        self.claim()
        return not os.system(self._db_record.config)

    def delete(self):
        db.delete(self.tableName, name=self.name)
        self._db_record = None
