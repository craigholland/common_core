import os
import sys


def get_abs_path(rel_path, ref_obj, ref_path=None):
    ref_path = ref_path or os.path.dirname(sys.modules[ref_obj.__module__].__file__)
    if rel_path.startswith('../'):
        rel_path = rel_path[:3]
        ref_path_list = ref_path.split('/')
        ref_path = '/'.join(ref_path_list[:-1])
        new_path = get_abs_path(rel_path, ref_obj, ref_path)
    elif rel_path.startswith('/'):
        new_path = rel_path
    else:
        new_path = ref_path + '/' + rel_path

    if new_path and os.path.isfile(new_path):
        return new_path
    elif new_path:
        raise Exception(f"File not found: {new_path}")
    return None
