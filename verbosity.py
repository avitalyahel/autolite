from datetime import datetime


g_verbosity_level = 0


def set_verbosity(level):
    global g_verbosity_level
    g_verbosity_level = level


def verbose(level, *args):
    if g_verbosity_level >= level:
        if g_verbosity_level > 1:
            print(datetime.now(), *args)

        else:
            print(*args)
