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
            raise UserWarning('You have already acquired: ' + self.name)

        else:
            raise PermissionError('already acquired by: ' + self._db_record.user)

    def release(self, force: bool = False):
        if not self._db_record.user:
            raise UserWarning('already free: ' + self.name)

        elif self._db_record.user != active_user_name() and not force:
            raise PermissionError('acquired by other: {}'.format(self._db_record.user))

        else:
            self._db_record.user = ''
            db.update(self.tableName, name=self.name, user=self._db_record.user)

    def install(self):
        assert not os.system(self._db_record.installer)

    def clean(self):
        assert not os.system(self._db_record.cleaner)

    def monitor(self):
        return not os.system(self._db_record.monitor)

    def config(self):
        return not os.system(self._db_record.config)

    def delete(self):
        db.delete(self.tableName, name=self.name)
        self._db_record = None
