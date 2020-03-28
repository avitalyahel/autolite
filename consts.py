import os


def get_self_path_dir(this_file: str) -> (str, str, str):
    self_abs_path = os.path.realpath(this_file)
    self_full_dir = os.path.dirname(self_abs_path)
    self_sub_dir = os.path.basename(self_full_dir)
    return self_abs_path, self_full_dir, self_sub_dir
