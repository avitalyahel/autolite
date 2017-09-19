'''
autolite installation tool.

Usage:
    install [--verify] [-v | -vv | -vvv]

Options:
    -h --help               Show this screen.
    -v --verbose            Higher verbosity messages.
    --verify                Only verify, without installing missing packagaes.
'''

import os
import sys
import argparse
import subprocess

import consts
from verbosity import verbose, set_verbosity
from dependencies import DEPENDENCIES

_, SELF_FULL_DIR, _ = consts.get_self_path_dir(__file__)

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', dest='verbose', action="store_true", help='Higher verbosity messages')
parser.add_argument('--verify', dest='verify', action="store_true", help='Only verify, without installing missing packagaes')
arguments = parser.parse_args()

def system_out(*cmd):
    return subprocess.run(
        ' '.join(cmd), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    ).stdout


def read_pip_list_dict() -> dict():
    return dict(entry.split(' ') for entry in system_out('pip3 list').split('\n') if entry)


def missing_iter():
    installed = read_pip_list_dict()

    for package, version in DEPENDENCIES.items():
        try:
            assert installed[package] >= '({})'.format(version)
            verbose(1, 'installed: {}.'.format(_pip_entry(package, version)))

        except (KeyError, AssertionError):
            yield package, version


def install():
    failed = {}

    for package, version in missing_iter():
        verbose(1, 'missing: {} - installing...'.format(_pip_entry(package, version)))

        if os.system('pip3 install {pkg}=={ver}'.format(pkg=package, ver=version)):
            verbose(1, '[!] failed installation of package: ' + _pip_entry(package, version))
            failed.update({package: version})

    if failed:
        print('[x]', len(failed), 'failed installations')
        sys.exit(1)


def verify():
    missing = dict((pack, ver) for pack, ver in missing_iter())

    if missing:
        print('[x] missing packages:')
        print('\t' + '\n\t'.join(_pip_entry(*pv) for pv in missing.items()))
        sys.exit(1)


def _pip_entry(pack, ver):
    return '{} ({})'.format(pack, ver)


if __name__ == '__main__':
    set_verbosity(1 if arguments.verbose else 0)

    if arguments.verbose:
        print(arguments)

    if arguments.verify:
        verify()

    else:
        install()

    verbose(0, '[v] autolite is well installed.')
