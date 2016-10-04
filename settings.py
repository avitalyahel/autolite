import yaml
from contextlib import contextmanager

from common import AttrDict

SETTINGS_DEFAULT = 'settings-default.yaml'
SETTINGS_USER = SETTINGS_DEFAULT.replace('default', 'user')


def read() -> AttrDict:
    with open(SETTINGS_DEFAULT) as f:
        settings = yaml.load(f)

    try:
        with open(SETTINGS_USER) as f:
            setting_dict = yaml.load(f)

        if setting_dict:
            settings.update(setting_dict)

    except FileNotFoundError:
        open(SETTINGS_USER, 'w').close()

    return AttrDict(settings)


@contextmanager
def write_context():    # yield AttrDict()
    read()

    with open(SETTINGS_USER) as f:
        setting_dict = yaml.load(f)
        user_settings = AttrDict(setting_dict) if setting_dict else AttrDict()

    yield user_settings

    with open(SETTINGS_USER, 'w') as f:
        yaml.dump(dict(user_settings), f, default_flow_style=False)
