import sys

import yaml

import common
import consts
import db
import schema
from system import System

SELF_ABS_PATH, SELF_FULL_DIR, SELF_SUB_DIR = consts.get_self_path_dir(__file__)
PACKAGE_NAME = SELF_SUB_DIR


def menu(arguments):
    if arguments['list']:
        if arguments['--YAML'] or arguments['--JSON']:
            where = dict(name=arguments['<name>']) if arguments['<name>'] else dict()
            systems = System.list(**where)
            common.dump(systems, toyaml=arguments['--YAML'], tojson=arguments['--JSON'],
                        entry=lambda item: item.__dict__)

        else:
            _system_list_table(arguments)

    elif system_execute(arguments):
        pass

    else:
        try:
            if arguments['create']:
                System.create(**_system_create_kwargs(arguments))
                arguments['--long'] = True
                _system_list_table(arguments)

            elif arguments['read']:
                system_read(arguments)

            elif arguments['set']:
                system_set(arguments)

            elif arguments['delete']:
                System(arguments['<name>']).delete()

        except NameError as exc:
            print(PACKAGE_NAME, 'Error!', exc)
            sys.exit(1)


def system_read(arguments):
    system = System(arguments['<name>'])
    toyaml, tojson = arguments['--YAML'], arguments['--JSON']

    if toyaml or tojson:
        common.dump([system.__dict__], toyaml, tojson, squash=True)

    else:
        print(system)


def _system_create_kwargs(arguments):
    kwargs = schema.TABLE_SCHEMAS.systems.new()

    if arguments['--fields']:
        with open(arguments['--fields']) as f:
            kwargs.update(yaml.safe_load(f))

    kwargs.update(dict((k, arguments['--' + k] or kwargs[k]) for k in kwargs.keys() if ('--' + k) in arguments))
    kwargs.update(
        name=arguments['<name>'],
        ip=arguments['<ip>'],
    )

    return kwargs


def _system_list_table(arguments):
    if arguments['--long']:
        col_names = 'name ip user installer cleaner config monitor comment'.split(' ')

    elif arguments['--fields']:
        col_names = arguments['--fields'].lower().split(',')

    else:
        col_names = ['name']

        if not arguments['--col-1']:
            col_names += ['user', 'comment']

    where = dict(name=arguments['<name>']) if arguments['<name>'] else dict()
    systems = db.list_table('systems', **where)
    rows = ([system[col] for col in col_names] for system in systems)

    col_titles = [name.upper() for name in col_names]
    common.print_table(col_titles, sorted(rows, key=lambda row: row[0]))


def system_set(arguments):
    kwargs = dict(
        (field, arguments['<exe>'])
        for field in ['installer', 'monitor', 'cleaner', 'config']
        if arguments[field]
    )

    if not kwargs:
        if arguments['ip']:
            kwargs.update(ip=arguments['<ip>'])

        if arguments['comment']:
            kwargs.update(comment=arguments['<text>'])

    db.update('systems', name=arguments['<name>'], **kwargs)
    arguments['--fields'] = 'name,' + ','.join(kwargs.keys())
    _system_list_table(arguments)


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
