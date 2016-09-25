import sys

import db
import consts
from system import System
from common import print_table

SELF_ABS_PATH, SELF_FULL_DIR, SELF_SUB_DIR = consts.get_self_path_dir(__file__)
PACKAGE_NAME = SELF_SUB_DIR


def menu(arguments):
    if arguments['list']:
        system_list()

    elif system_execute(arguments):
        pass

    else:
        try:
            if arguments['create']:
                System.create(**_system_create_kwargs(arguments))

            elif arguments['read']:
                print(System(arguments['<name>']))

            elif arguments['set']:
                system_set(arguments)

            elif arguments['delete']:
                System(arguments['<name>']).delete()

            elif arguments['reset']:
                system_reset(arguments)

        except NameError as exc:
            print(PACKAGE_NAME, 'Error!', exc)
            sys.exit(1)


def _system_create_kwargs(arguments):
    return dict(
        name=arguments['<name>'],
        ip=arguments['<ip>'],
        installer=arguments['--installer'],
        monitor=arguments['--monitor'],
        cleaner=arguments['--cleaner'],
        config=arguments['--config'],
    )


def system_list():
    titles = str(db.g_table_info.systems).upper().split('|')
    print_table(titles, db.rows('systems'))


def system_set(arguments):
    kwargs = dict(
        (field, arguments['<exe>'])
        for field in ['installer', 'monitor', 'cleaner', 'config']
        if arguments[field]
    )

    if not kwargs and arguments['ip']:
        kwargs.update(ip=arguments['<ip>'])

    db.update('systems', name=arguments['<name>'], **kwargs)


def system_execute(arguments) -> bool:
    if arguments['set']:
        return False

    for cmd in 'acquire | release | install | clean | monitor | config'.split(' | '):
        if arguments[cmd]:
            try:
                system = System(arguments['<name>'])
                kwargs = dict(force=arguments['--force']) if cmd == 'release' else dict()
                getattr(system, cmd)(**kwargs)

            except PermissionError as exc:
                print(PACKAGE_NAME, 'Error!', exc)
                sys.exit(1)

            except Exception as exc:
                if type(exc).__name__.endswith('Warning'):
                    print(PACKAGE_NAME, 'Warning:', exc)

                else:
                    raise

            return True

    return False
