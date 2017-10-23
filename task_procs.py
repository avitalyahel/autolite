import os
import subprocess

import db
from task import Task
from verbosity import verbose

g_procs = {}


LOG_ROOT = '/var/log/autolite'

def start(task: Task):
    task.start()

    log_path = os.path.join(LOG_ROOT, db.name())
    os.makedirs(log_path, exist_ok=True)
    logfile = open('{path}/{task_name}.log'.format(path=log_path, task_name=task.name), 'w')
    new_task_proc = subprocess.Popen('export AUTOLITE_TASK_NAME="{}" ; '.format(task.name) + task.command, 
                                     shell=True, universal_newlines=True, stdout=logfile, stderr=logfile)
    new_task_proc.stdout=logfile

    g_procs.update({task.name: new_task_proc})
    verbose(2, 'proc pool added with:', new_task_proc)


def serve(timeout: int) -> int:
    completed = []

    for task_name, proc in g_procs.items():
        task = Task(task_name)
        proc.poll()

        if proc.returncode is not None:
            if proc.returncode:
                task.fail()

            else:
                task.reset()

            completed += [task_name]

        elif timeout and task.expired(timeout):
            _terminate_and_fail(task, timeout)
            completed += [task_name]

    for task in completed:
        g_procs[task].stdout.close()
        del g_procs[task]

    return len(g_procs)


def _terminate_and_fail(task: Task, timeout: int):
    verbose(0, 'task', task.name, 'timed-out after', timeout, 'sec, terminating...')
    g_procs[task.name].terminate()
    verbose(2, 'proc terminated, task:', task.name)
    task.fail()
