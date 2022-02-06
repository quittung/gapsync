from multiprocessing.pool import Pool
import os, shutil

from .serialize import load_json
from .hashing import hash_folder

def scan_or_load(path: str, pool = None, verbose: bool = False) -> dict:
    if type(path) == dict:
        return path
    elif os.path.isdir(path):
        return hash_folder(path, pool, verbose)
    else: 
        return load_json(path)

def dir_content_same(path_a: str, path_b: str, pool: Pool, verbose: bool = False):
    return scan_or_load(path_a, pool, verbose) == scan_or_load(path_b, pool, verbose)

def all_files_exist(dir:str, file_list: list):
    return all(os.path.exists(os.path.join(dir, file)) for file in file_list)

def make_patch_instructions(source_list: dict, target_list: dict):
    """
    possible combinations
    file in both and same           ignore
    file in both and different      copy
    file only in target             delete
    file only in source             copy
    """

    files_source = set(source_list)
    files_target = set(target_list)

    files_common = files_source.intersection(files_target)
    files_source_only = files_source - files_target
    files_target_only = files_target - files_source

    files_common_same = set(f for f in files_common if source_list[f] == target_list[f])
    files_common_different = files_common - files_common_same

    files_copy = files_common_different.union(files_source_only)
    files_delete = files_target_only

    return {"copy": list(files_copy), "delete": list(files_delete)}

def copy_list(source: str, target: str, files: list):
    for f in files:
        file_source = os.path.join(source, f)
        file_dest = os.path.join(target, f)

        os.makedirs(os.path.dirname(file_dest), exist_ok=True)
        shutil.copy(file_source, file_dest)

def delete_list(dir: str, files: list):
    for f in files:
        path = os.path.join(dir, f)
        os.remove(path)

        path_dir = os.path.dirname(path)
        if not os.listdir(path_dir):
            os.rmdir(path_dir)

def patch(source: str, target: str, instructions: dict):
    copy_list(source, target, instructions["copy"])
    delete_list(target, instructions["delete"])