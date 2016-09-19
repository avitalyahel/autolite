import io
import sys
import itertools
import subprocess
from contextlib import contextmanager, redirect_stdout


class AttrDict(dict):

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value


def system_out(cmd):
    return subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    ).stdout


@contextmanager
def redirected_stdout_context(*cli) -> io.StringIO:
    sys.argv = []
    for c in cli:
        sys.argv += c.split(' ')

    with io.StringIO() as buf, redirect_stdout(buf):
        yield buf


def fmtprint(values, formats=[], sep=' '):
    for val, fmt in itertools.zip_longest(values, formats, fillvalue='{}'):
        print(fmt.format(val), end=sep)
    print()
