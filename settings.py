import yaml
from contextlib import contextmanager

from common import AttrDict

SETTINGS_DEFAULT = 'settings-default.yaml'
SETTINGS_USER = SETTINGS_DEFAULT.replace('default', 'user')


def read() -> AttrDict:
    with open(SETTINGS_DEFAULT) as f:
        settings = AttrDict(yaml.load(f, Loader=yaml.FullLoader))

    try:
        with open(SETTINGS_USER) as f:
            setting_dict = yaml.load(f, Loader=yaml.FullLoader)

    except FileNotFoundError:
        open(SETTINGS_USER, 'w').close()

    else:
        if setting_dict is not None:
            settings.update(setting_dict)

    return settings


@contextmanager
def write_context():    # yield AttrDict()
    assert read(), 'unexpected empty settings'

    with open(SETTINGS_USER) as f:
        setting_dict = yaml.load(f, Loader=yaml.FullLoader)
        user_settings = AttrDict(setting_dict) if setting_dict else AttrDict()

    yield user_settings

    updated = yaml.dump(user_settings.__dict__, default_flow_style=False)
    with open(SETTINGS_USER, 'w') as f:
        f.write(updated)
