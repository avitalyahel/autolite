import subprocess
from datetime import datetime

import db
from schema import TableSchema
from verbosity import verbose

g_procs = {}


def start(task: TableSchema):
    db.update_task(name=task.name, state='running', last=datetime.now())
    g_procs.update({task.name: subprocess.Popen(task.command, shell=True, universal_newlines=True)})
    verbose(2, 'proc pool added with:', g_procs[task.name])


def serve(timeout: int) -> int:
    completed = []

    for task_name, proc in g_procs.items():
        proc.poll()

        if proc.returncode is not None:
            db.update_task(name=task_name, state='failed' if proc.returncode else 'pending')
            completed += [task_name]

        elif timeout:
            task = db.read_task(task_name)

            if db.is_timed_out(task, timeout):
                _terminate_and_fail(task, timeout)
                completed += [task_name]

    for task in completed:
        del g_procs[task]

    return len(g_procs)


def _terminate_and_fail(task: TableSchema, timeout: int):
    verbose(0, 'task', task.name, 'timed-out after', timeout, 'sec - failing!')
    proc = g_procs[task.name]
    proc.terminate()
    verbose(2, 'proc terminated, task:', task.name)
    db.update_task(name=task.name, state='failed')
