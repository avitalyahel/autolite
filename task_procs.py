import os
import subprocess

import db
from task import Task
from verbosity import verbose

LOG_ROOT = '/var/log/autolite'


g_procs = {}


def start(task: Task):
    global g_procs
    g_procs.update({task.name: _new_task_proc(task)})
    verbose(2, 'proc pool added with:', g_procs[task.name])
    task.start()


def serve(timeout: int) -> int:
    global g_procs

    completed = []

    for task_name, proc in g_procs.items():
        task = Task(task_name)
        task.reload()
        proc.poll()

        if proc.returncode is not None:
            if proc.returncode:
                if proc.returncode == 126:  # bash error code for "Command invoked cannot execute"
                    task.skip()
                    verbose(1, task.name, 'skipped')

                else:
                    task.fail()
                    verbose(1, task.name, 'failed')

            elif task.once:
                task_name = task.name
                task.delete()
                verbose(1, task_name, 'delete')

            else:
                task.reset()
                verbose(1, task.name, 'reset')

            completed += [task_name]

        elif timeout and task.expired(timeout):
            _terminate_and_fail(task, timeout)
            completed += [task_name]

    for task in completed:
        g_procs[task].stdout.close()
        del g_procs[task]

    return len(g_procs)


def _new_task_proc(task: Task) -> subprocess.Popen:
    logfile = open(_new_log_path(task), 'w', 1)
    result = subprocess.Popen('''
if [ -e ~/.bashrc ]
then
    . ~/.bashrc
elif [ -e ~/.bash_profile ]
then
    . ~/.bash_profile
fi
export AUTOLITE_TASK_NAME="{}"
'''.format(task.name) + task.command,
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
