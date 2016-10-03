import sys

import db
import consts
import common
from system import System

SELF_ABS_PATH, SELF_FULL_DIR, SELF_SUB_DIR = consts.get_self_path_dir(__file__)
PACKAGE_NAME = SELF_SUB_DIR


def menu(arguments):
    if arguments['list']:
        if arguments['--YAML']:
            common.dump(System.list(), fmt='YAML', entry=lambda item: {item.name: dict(item.__dict__)})

        elif arguments['--JSON']:
            common.dump(System.list(), fmt='JSON', entry=lambda item: {item.name: item.__dict__})

        else:
            system_list_table(arguments)

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


def system_list_table(arguments):
    if arguments['--long']:
        col_names = db.g_table_columns.systems.names
        rows = db.rows('systems')

    else:
        col_names = ['name', 'user']
        systems = db.list_table('systems')
        rows = ([task[col] for col in col_names] for task in systems)

    col_titles = [name.upper() for name in col_names]
    common.print_table(col_titles, rows)


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
                cmd_method = getattr(system, cmd)
                kwargs = dict(force=arguments['--force']) if cmd == 'release' else dict()
                cmd_method(**kwargs)

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
