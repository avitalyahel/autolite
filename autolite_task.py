import sys
from collections import Counter
from datetime import datetime

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


def task_lineage(arguments):
    name = arguments['<name>']

    def lineage_filter(task: Task):
        return _holdings_filter(task, arguments)

    if arguments['--YAML'] or arguments['--JSON']:
        common.dump(_task_lineage_dicts(parent=name, task_filter=lineage_filter), 
            toyaml=arguments['--YAML'], 
            tojson=arguments['--JSON'],
        )

    else:
        _print_task_lineage(_task_lineage_dicts(parent=name, task_filter=lineage_filter), long=arguments['--long'])


def _holdings_filter(task: Task, arguments: dict) -> bool:
    return (arguments['--holding'] is None or task.holdingAny(arguments['--holding'])) \
       and (arguments['--not-holding'] is None or not task.holdingAny(arguments['--not-holding']))


def _task_create_kwargs(arguments):
    result = AttrDict(
        name=arguments['<name>'],
        state='pending',
        command=arguments['--command'],
        condition=arguments['--condition'],
        last=str(datetime.now()),
    )

    if arguments['--once']:
        result.last += '<once>'

    if arguments['--inherit']:
        parent = db.read(table='tasks', name=arguments['--inherit'])
        result.update(dict(
            parent=parent.name,
            schedule='<inherit>',
            command=result.command if result.command else '<inherit>',
            email='<inherit>',
            condition=result.condition if result.condition else '<inherit>',
        ))

    result.update(_task_sched_kwargs(arguments))

    return result


def _task_sched_kwargs(arguments):
    for sched in schema.SCHEDULES:
        if arguments['--' + sched]:
            return dict(schedule=sched)

    return dict()


def _task_lineage_dicts(parent: str = '', task_filter = lambda task: True) -> [dict]:
    tasks = []
    stack = [tasks]

    def _push_subtasks():
        last_task = stack[-1][-1] if len(stack[-1]) else dict()
        last_task['~subtasks'] = []
        stack.append(last_task['~subtasks'])

    def _pop_subtasks():
        stack.pop()
        last_task = stack[-1][-1] if len(stack[-1]) else dict()

        if '~subtasks' in last_task:
            last_task['~summary'] = _state_summary_dict(last_task['~subtasks'])

    for task, level in Task.walkIter(parent=parent):
        while level > len(stack) - 1:
            _push_subtasks()

        while level < len(stack) - 1:
            _pop_subtasks()

        if task_filter(task):
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
        tasks = ({t.name: t.__dict__} for t in filter(lambda t: _holdings_filter(t, arguments), Task.list()))
        common.dump(tasks, toyaml=arguments['--YAML'], tojson=arguments['--JSON'])

    else:
        _task_list_table(arguments)


def _task_list_table(arguments):
    if arguments['--col-1']:
        col_names = ['name']

    elif arguments['--long']:
        col_names = 'name parent schedule state command condition resources email log last'.split(' ')

    elif arguments['--fields']:
        col_names = arguments['--fields'].lower().split(',')

    else:
        col_names = 'name state schedule log last'.split(' ')

    if arguments['--ancestor']:
        tasks = filter(lambda rec: _holdings_filter(Task(record=rec), arguments), db.list_table('tasks'))
        tasks = filter(lambda task: _decendant_filter(task, arguments['--ancestor']), tasks)

    else:
        where = dict(name=arguments['<name>']) if arguments['<name>'] else dict()
        tasks = filter(lambda rec: _holdings_filter(Task(record=rec), arguments), db.list_table('tasks', **where))

    rows = ([task[col] for col in col_names] for task in tasks)

    common.print_table([name.upper() for name in col_names], rows)


def _decendant_filter(task: Task, ancestor: str) -> bool:
    parent = task.parent

    while parent != "":
        if parent == ancestor:
            return True

        parent = db.read(table='tasks', name=parent).parent

    return False


def task_set(arguments):
    if arguments['schedule']:
        kwargs = _task_sched_kwargs(arguments)

    elif arguments['parent']:
        kwargs = dict(parent=arguments['<parent>'])

    elif arguments['email']:
        kwargs = dict(email=arguments['<email>'])

    elif arguments['resources']:
        kwargs = dict(resources=arguments['<resources>'])

    elif arguments['log']:
        kwargs = dict(log=arguments['<text>'])

    else:
        kwargs = dict(
            (field, arguments['<exe>'])
            for field in ['condition', 'command']
            if arguments[field]
        )

    assert kwargs, 'unexpected empty attrs to set for tasks'

    db.update('tasks', name=arguments['<name>'], **kwargs)
    print(Task(arguments['<name>']))


def task_reset(arguments):
    task = Task(arguments['<name>'])

    if task.pending:
        verbose(1, 'task', task.name, 'already pending.')
        return

    if not arguments['--force'] and not task.failed:
        print(PACKAGE_NAME, 'Error! Task', task.name, 'must be failed before reset.')
        sys.exit(1)

    task.reset()
