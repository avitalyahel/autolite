from contextlib import contextmanager

from datetime import datetime


g_verbosity_level = 0


def set_verbosity(level: int):
    if level >= 0:
        global g_verbosity_level
        g_verbosity_level = level


def get_verbosity_level() -> int:
    return g_verbosity_level


def verbose(level: int, *args):
    if g_verbosity_level >= level:
        if g_verbosity_level > 1:
            print(datetime.now(), *args)

        else:
            print(*args)


@contextmanager
def verbosity_context(level: int):
    original = get_verbosity_level()
    set_verbosity(level)

    yield

    set_verbosity(original)
