import subprocess

from task import Task
from verbosity import verbose

g_procs = {}


def start(task: Task):
    if not task.condition:
        verbose(2, 'condition not met for:', task.name)
        return

    task.start()
    g_procs.update({task.name: subprocess.Popen(task.command, shell=True, universal_newlines=True)})
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
        del g_procs[task]

    return len(g_procs)


def _terminate_and_fail(task: Task, timeout: int):
    verbose(0, 'task', task.name, 'timed-out after', timeout, 'sec, terminating...')
    g_procs[task.name].terminate()
    verbose(2, 'proc terminated, task:', task.name)
    task.fail()
