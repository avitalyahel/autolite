import sys
import yaml
import json

import db
import consts
import schema
import common
from task import Task
from verbosity import verbose

SELF_ABS_PATH, SELF_FULL_DIR, SELF_SUB_DIR = consts.get_self_path_dir(__file__)
PACKAGE_NAME = SELF_SUB_DIR


def menu(arguments):
    if arguments['list']:
        if arguments['--recursive']:
            task_lineage(arguments)

        else:
            task_list(arguments)

    else:
        try:
            if arguments['create']:
                Task.create(**_task_create_kwargs(arguments))

            elif arguments['read']:
                print(Task(arguments['<name>']))

            elif arguments['set']:
                task_set(arguments)

            elif arguments['delete']:
                Task(arguments['<name>']).delete()

            elif arguments['reset']:
                task_reset(arguments)

        except NameError as exc:
            print(PACKAGE_NAME, 'Error!', exc)
            sys.exit(1)


def _task_create_kwargs(arguments):
    result = dict(
        name=arguments['<name>'],
        state='pending',
        setup=arguments['--setup'],
        command=arguments['--command'],
        teardown=arguments['--teardown'],
    )

    result.update(_task_sched_kwargs(arguments))

    return result


def _task_sched_kwargs(arguments):
    for sched in schema.SCHEDULES:
        if arguments['--' + sched]:
            return dict(schedule=sched)

    return dict()


def task_lineage(arguments):
    tasks = []
    stack = [tasks]

    for task, level in Task.walkIter(parent=''):
        if any(arguments[flag] for flag in ['--YAML', '--JSON']):
            while level > len(stack) - 1:
                last_dict = stack[-1][-1]
                last_dict['~subtasks'] = []
                stack.append(last_dict['~subtasks'])

            while level < len(stack) - 1:
                stack.pop()

            stack[-1] += [task.__dict__]

        else:
            _print_subtask(arguments, task, level)

    if arguments['--YAML']:
        common.dump(tasks, fmt='YAML')

    elif arguments['--JSON']:
        common.dump(tasks, fmt='JSON')


def _print_subtask(arguments, task, level):
    tabs = (' ' * 4 * level)
    print(tabs, end='')

    if arguments['--long']:
        print(tabs + task.name, ', '.join('{}: {}'.format(k, v) for k, v in task.items() if v and k != 'name'))

    else:
        print(tabs + '{}: {}'.format(task.name, task.state))


def task_list(arguments):
    if arguments['--YAML']:
        print(yaml.dump([{t.name: t.__dict__} for t in Task.list()],
                        default_flow_style=False))

    elif arguments['--JSON']:
        print(json.dumps([{t.name: t.__dict__} for t in Task.list()],
                         indent=4))

    else:
        task_list_table(arguments)


def task_list_table(arguments):
    if arguments['--long']:
        col_names = db.g_table_columns.tasks.names
        rows = db.rows('tasks')

    else:
        col_names = ['name', 'state']
        tasks = db.list_table('tasks')
        rows = ([task[col] for col in col_names] for task in tasks)

    col_titles = [name.upper() for name in col_names]
    common.print_table(col_titles, rows)


def task_set(arguments):
    if arguments['schedule']:
        kwargs = _task_sched_kwargs(arguments)

    elif arguments['parent']:
        kwargs = dict(parent=arguments['<parent>'])

    else:
        kwargs = dict(
            (field, arguments['<exe>'])
            for field in ['setup', 'command', 'teardown']
            if arguments[field]
        )

    assert kwargs, 'unexpected empty attrs to set for tasks'

    db.update('tasks', name=arguments['<name>'], **kwargs)


def task_reset(arguments):
    task = Task(arguments['<name>'])

    if task.pending:
        verbose(1, 'task', task.name, 'already pending.')
        return

    if not arguments['--force'] and not task.failed:
        print(PACKAGE_NAME, 'Error! Task', task.name, 'must be failed before reset.')
        sys.exit(1)

    task.reset()
