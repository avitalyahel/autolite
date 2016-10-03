import io
import sys
import yaml
import json
import getpass
import itertools
import subprocess
from contextlib import contextmanager, redirect_stdout


class AttrDict(dict):

    def __getattr__(self, name):
        try:
            return self[name]

        except KeyError:
            return self.__getattribute__(name)

    def __setattr__(self, name, value):
        self[name] = value


def system_out(*cmd):
    return subprocess.run(
        ' '.join(cmd), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    ).stdout


@contextmanager
def redirected_stdout_context(*cli) -> io.StringIO:
    sys.argv = []
    for c in cli:
        if c:
            sys.argv += c.split(' ')

    with io.StringIO() as buf, redirect_stdout(buf):
        yield buf


def fmtprint(values, formats=[], sep=' '):
    for val, fmt in itertools.zip_longest(values, formats, fillvalue='{}'):
        print(fmt.format(val), end=sep)
    print()


def measure_column_widths(rows) -> list:
    widths = []

    for row in rows:
        for i, field in enumerate(row):
            try:
                widths[i] = max(widths[i], len(field))

            except IndexError:
                widths.insert(i, len(field))

    return widths


def print_table(titles: iter, rows: iter):
    taskiter1, taskiter2 = itertools.tee(rows)
    widths = (max(w1, w2) for w1, w2 in zip(measure_column_widths(taskiter1), measure_column_widths([titles])))
    formats = [str('{:%d}' % width) for width in widths]

    fmtprint(titles, formats, sep='  ')

    for _task in taskiter2:
        fmtprint(_task, formats, sep='  ')


def active_user_name() -> str:
    return getpass.getuser()


def dump(items: iter, fmt: str, entry=lambda item: item):
    if fmt == 'YAML':
        print(yaml.dump([entry(i) for i in items], default_flow_style=False))

    elif fmt == 'JSON':
        print(json.dumps([entry(i) for i in items], indent=4))

    else:
        raise KeyError('unsupported dump format: ' + fmt)
