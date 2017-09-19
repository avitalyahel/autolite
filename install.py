'''
autolite installation tool.

Usage:
    install [--verify] [-v | -vv | -vvv]

Options:
    -h --help               Show this screen.
    --version               Show version.
    -v --verbose            Higher verbosity messages.
    --verify                Only verify, without installing missing packagaes.
'''

import os
import sys

import consts
from common import system_out
from verbosity import verbose, set_verbosity
from dependencies import DEPENDENCIES

_, SELF_FULL_DIR, _ = consts.get_self_path_dir(__file__)


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
    from docopt import docopt

    with open(os.path.join(SELF_FULL_DIR, 'version')) as ver_file:
        arguments = docopt(__doc__, version=ver_file.read())

    set_verbosity(arguments['--verbose'])

    if arguments['--verbose'] > 1:
        print(arguments)

    if arguments['--verify']:
        verify()

    else:
        install()

    verbose(1, '[v] autolite is well installed.')
