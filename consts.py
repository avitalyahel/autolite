import os

DB_NAME = 'autolite.db'


def get_self_path_dir(this_file: str) -> (str, str, str):
    SELF_ABS_PATH = os.path.realpath(this_file)
    SELF_FULL_DIR = os.path.dirname(SELF_ABS_PATH)
    SELF_SUB_DIR = os.path.basename(SELF_FULL_DIR)
    return SELF_ABS_PATH, SELF_FULL_DIR, SELF_SUB_DIR
