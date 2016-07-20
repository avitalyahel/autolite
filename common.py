import subprocess


class AttrDict(dict):

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value


def system_out(cmd):
    return subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    ).stdout
