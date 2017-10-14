import sys
from collections import Counter

import db
import consts
import schema
import common
from task import Task
from common import AttrDict
from verbosity import verbose

SELF_ABS_PATH, SELF_FULL_DIR, SELF_SUB_DIR = consts.get_self_path_dir(__file__)
PACKAGE_NAME = SELF_SUB_DIR


def menu(arguments):
    if arguments['list']:
        if arguments['--recursive']:
            name = arguments['<name>']

            if arguments['--YAML'] or arguments['--JSON']:
                common.dump(_task_lineage_dicts(parent=name), toyaml=arguments['--YAML'], tojson=arguments['--JSON'])

            else:
                _print_task_lineage(_task_lineage_dicts(parent=name), long=arguments['--long'])

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
        command=arguments['--command'],
        condition=arguments['--condition'],
        last='<once>' if arguments['--once'] else None,
    )

    result.update(_task_sched_kwargs(arguments))

    return result


def _task_sched_kwargs(arguments):
    for sched in schema.SCHEDULES:
        if arguments['--' + sched]:
            return dict(schedule=sched)

    return dict()


def _task_lineage_dicts(parent: str = '') -> [dict]:
    tasks = []
    stack = [tasks]

    def _push_subtasks():
        last_task = stack[-1][-1]
        last_task['~subtasks'] = []
        stack.append(last_task['~subtasks'])

    def _pop_subtasks():
        stack.pop()
        last_task = stack[-1][-1]

        if '~subtasks' in last_task:
            last_task['~summary'] = _state_summary_dict(last_task['~subtasks'])

    for task, level in Task.walkIter(parent=parent):
        while level > len(stack) - 1:
            _push_subtasks()

        while level < len(stack) - 1:
            _pop_subtasks()

        stack[-1] += [task.__dict__]

    while 0 < len(stack) - 1:
        _pop_subtasks()

    if parent:
        parent_task = Task(name=parent).__dict__
        parent_task['~subtasks'] = tasks[:]
        parent_task['~summary'] = _state_summary_dict(parent_task['~subtasks'])
        tasks = [parent_task]

    return tasks


def _state_summary_dict(tasks: [dict]) -> dict:
    summary = Counter(dict(total=len(tasks)))

    for task in tasks:
        summary[task['state']] += 1

        if '~summary' in task:
            summary += Counter(task['~summary'])

    return dict(summary)


def _print_task_lineage(tasks: [dict], long: bool, level: int = 0):
    for task in tasks:
        _print_subtask(task, long, level)

        if '~subtasks' in task:
            _print_task_lineage(task['~subtasks'], long, level + 1)


def _print_subtask(task, long, indent):
    task = AttrDict(task)
    tabs = '  ' * indent
    print(tabs, end='')

    if long:
        print(task.name, ', '.join('{}: {}'.format(k, v) for k, v in task.items()
                                   if v and k != 'name' and k[0] != '~'),
              end='')

    else:
        print('{}: {}'.format(task.name, task.state), end='')

    if '~summary' in task:
        print('', _subtask_summary_repr(task['~summary']))

    else:
        print()


def _subtask_summary_repr(summary: dict) -> str:
    return '({} subtasks: {})'.format(
        summary['total'],
        ', '.join('{} {}'.format(v, k)
                  for k, v in summary.items()
                  if k != 'total')
    )


def task_list(arguments):
    if arguments['--YAML'] or arguments['--JSON']:
        common.dump([{t.name: t.__dict__} for t in Task.list()], toyaml=arguments['--YAML'], tojson=arguments['--JSON'])

    else:
        _task_list_table(arguments)


def _task_list_table(arguments):
    if arguments['--long']:
        col_names = db.g_table_columns.tasks.names
        rows = db.rows('tasks')

    else:
        col_names = ['name', 'state', 'schedule', 'last']
        tasks = db.list_table('tasks')
        rows = ([task[col] for col in col_names] for task in tasks)

    col_titles = [name.upper() for name in col_names]
    common.print_table(col_titles, rows)


def task_set(arguments):
    if arguments['schedule']:
        kwargs = _task_sched_kwargs(arguments)

    elif arguments['parent']:
        kwargs = dict(parent=arguments['<parent>'])

    elif arguments['email']:
        kwargs = dict(email=arguments['<email>'])

    else:
        kwargs = dict(
            (field, arguments['<exe>'])
            for field in ['condition', 'command']
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
