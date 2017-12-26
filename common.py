import io
import os
import sys
import yaml
import json
import getpass
import itertools
import subprocess
from contextlib import contextmanager, redirect_stdout


class AttrDict(dict):

    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            for k, v in args[0].items():
                self[k] = AttrDict(v) if isinstance(v, dict) else v

        else:
            super(AttrDict, self).__init__(*args, **kwargs)

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value

    def update(self, keyvalues: dict):
        for k, v in keyvalues.items():
            if k in self and isinstance(v, dict):
                self[k].update(v)

            else:
                self[k] = v

    @property
    def __dict__(self):
        return dict((k, v.__dict__ if isinstance(v, type(self)) else v) for k, v in self.items())


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


def dump(items: iter, toyaml: bool = False, tojson: bool = False, squash: bool = False, entry=lambda item: item):
    entries = [entry(i) for i in items]

    if squash and len(entries) == 1:
        entries = entries[0]

    if toyaml:
        print(yaml.dump(entries, default_flow_style=False))

    if tojson:
        print(json.dumps(entries, indent=4))


@contextmanager
def chdir_context(new_dir: str):
    old_dir = os.getcwd()
    os.chdir(new_dir)
    try:

        yield

    finally:
        os.chdir(old_dir)
