import os
import subprocess

import db
from task import Task
from verbosity import verbose

LOG_ROOT = '/var/log/autolite'


g_procs = {}


def start(task: Task):
    task.start()
    g_procs.update({task.name: _new_task_proc(task)})
    verbose(2, 'proc pool added with:', g_procs[task.name])


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


def _new_task_proc(task: Task) -> subprocess.Popen:
    logfile = open(_new_log_path(task), 'w')
    result = subprocess.Popen('export AUTOLITE_TASK_NAME="{}" ; '.format(task.name) + task.command, 
                              shell=True, universal_newlines=True, stdout=logfile, stderr=logfile)
    result.stdout = logfile
    return result


def _new_log_path(task: Task) -> str:
    log_path = os.path.join(LOG_ROOT, db.name())
    os.makedirs(log_path, exist_ok=True)
    return '{path}/{task_name}.log'.format(path=log_path, task_name=task.name)


def _terminate_and_fail(task: Task, timeout: int):
    verbose(0, 'task', task.name, 'timed-out after', timeout, 'sec, terminating...')
    g_procs[task.name].terminate()
    verbose(2, 'proc terminated, task:', task.name)
    task.fail()
