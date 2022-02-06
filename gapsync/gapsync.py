import os, sys, shutil
import argparse, json
import hashlib
import multiprocessing

BUFFERSIZE = 1024 * 1024 #* 128

def hash_file(filename: str) -> str:
    hash = hashlib.sha256()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(BUFFERSIZE)
            if not data:
                break
            hash.update(data)

    return hash.hexdigest()

class HashFileAsyncWrap(object):
    def __init__(self, verbose) -> None:
        self.verbose = verbose
    
    def __call__(self, filename) -> str:
        hash = hash_file(filename)
        if self.verbose: print("{} - {}\n".format(hash, filename), end="")
        return hash

def hash_folder(top_dir: str, verbose: bool = False) -> dict:
    file_dict = {}
    top_dir = os.path.normpath(top_dir)
    top_dir_len = len(top_dir)
    
    files = [os.path.join(root, file) for root, dirs, files in os.walk(top_dir) for file in files]

    hash_file_async = HashFileAsyncWrap(verbose)
    hashes = pool.map(hash_file_async, files)

    files = [file[len(top_dir):] for file in files]
    files = [file.replace("\\", "/") for file in files]
    files = [file[1:] if file[0] == "/" else file for file in files]
    file_dict = dict(zip(files, hashes))
    
    return file_dict
    
def dump_json(obj: object, fname: str) -> None:
    """Dumps an object to a json file.

    Args:
        obj (Any): Object to encode.
        fname (str): Filename of json file.
    """   
    dirname = os.path.dirname(fname)
    if dirname != "" and not os.path.exists(dirname): os.makedirs(dirname)
    
    with open(fname, 'w') as fobj:
        json.dump(obj, fobj, indent = 4)

def load_json(fname: str) -> object:
    """Loads a json file and returns the encoded object.

    Args:
        fname (str): Path to json file.

    Returns:
        Any: Object encoded in json file.
    """    
    with open(fname, 'r') as fobj:
        return json.loads(fobj.read())

def print_json(obj: object) -> None:
    print(json.dumps(obj, indent=4))

def scan_or_load(path: str) -> dict:
    if os.path.isdir(path):
        return hash_folder(path)
    else: 
        return load_json(path)

def verify_dir(path_a: str, path_b: str):
    return scan_or_load(path_a) == scan_or_load(path_b)

def verify_files(dir:str, file_list: list):
    return all(os.path.exists(os.path.join(dir, "files", file)) for file in file_list)

def compare(source_list: dict, target_list: dict):
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


if __name__ == '__main__':  
    #multiprocessing.freeze_support()
    pool = multiprocessing.Pool()

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("primary", help="primary path")
    parser.add_argument("secondary", nargs="?", help="secondary path")
    parser.add_argument("-o", "--out", help="output path for json files (scan or patch instructions)")
    parser.add_argument("-d", "--data", help="data directory")
    parser.add_argument("-p", "--patch", action='store_true', help="actually modify the target directory")
    parser.add_argument("-v", "--verbose", action='store_true')

    parser.description = "tool for synchronizing two directories across different systems without simultaneous access\nworks with airgapped systems and only sends changed files"
    parser.epilog = "\
if both directories are mounted on your system:\n\
    python3 gapsync.py *source_dir* *target_dir* -p\n\
    \n\
if the directories are on separate systems, follow this three step process:\n\
    1. scanning the target directory\n\
        python3 gapsync.py *target_dir* -o scan.json\n\
        this creates a list of files and their hashes and saves it as 'scan.json'\n\
        send this file to the person performing step 2\n\
    2. preparing the patch data\n\
        python3 gapsync.py *source_dir* scan.json -d *data_dir*\n\
        this compares the source data to the scan of the target data\n\
        then it collects all necessary data in *data_dir*\n\
        send that directory to the person performing the next step\n\
    3. patching the target directory\n\
        python3 gapsync.py *target_dir* -d *data_dir* -p\n\
        this checks the data directory and applies the patch\n\
        then it verifies the target directory is identical to the source\n\
        to perform a dry run without changing files, remove the '-p'"

    args = parser.parse_args()


    if not args.secondary:
        # only one dir given
        if args.data: 
            # data dir given, prepare to patch 
            if not verify_dir(args.primary, os.path.join(args.data, "before.json")):
                print("ERROR: target dir has changed after creating the patch")
                sys.exit(1)
                
            patch_instructions = load_json(os.path.join(args.data, "patch.json"))
            if not verify_files(args.data, patch_instructions["copy"]):
                print("ERROR: files missing from data folder")
                sys.exit(1)

            print_json(patch_instructions)
            if args.patch:
                patch(
                    os.path.join(args.data, "files"),
                    args.primary,
                    patch_instructions
                )

                
                if not verify_dir(args.primary, os.path.join(args.data, "after.json")):
                    print("ERROR: target dir does not match source after patching")
                    sys.exit(1)
                else:
                    print("patched and verified")
            else:
                print("data folder verified, ready for patching with option '-p'")
            
        else:
            # scan that dir
            file_list = hash_folder(args.primary, args.verbose)
            print_json(file_list)
            if args.out:
                dump_json(file_list, args.out)
    else:
        # two dirs given
        source_list = scan_or_load(args.primary)
        target_list = scan_or_load(args.secondary)
        patch_instructions = compare(source_list, target_list)

        print_json(patch_instructions)
        if args.out:
            dump_json(patch_instructions, args.out)

        if args.data:
            dump_json(target_list, os.path.join(args.data, "before.json"))
            dump_json(source_list, os.path.join(args.data, "after.json"))
            dump_json(patch_instructions, os.path.join(args.data, "patch.json"))
            copy_list(args.primary, os.path.join(args.data, "files"), patch_instructions["copy"])

        if args.patch:
            patch(
                args.primary,
                args.secondary,
                patch_instructions
            )

            if not verify_dir(args.primary, args.secondary):
                print("ERROR: target dir does not match source after patching")
                sys.exit(1)
            else:
                print("patched and verified")
