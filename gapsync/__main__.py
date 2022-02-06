import argparse, os, sys
from multiprocessing.pool import Pool

import core

from serialize import dump_json, print_json
def parse_args():
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
        python3 gapsync.py *target_dir* -o target.json\n\
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

    return parser.parse_args()

def single_dir_mode(dir: str, out: str, verbose: bool):
    """this mode only supports scanning a single directory and outputting the result"""
    file_list = core.scan_or_load(dir)
    print_json(file_list)
    
    if out:
        dump_json(file_list, out)

def dual_dir_mode(source: str, target: str, out: str, data: str, make_data: bool, patch: bool, verbose: bool):
    source_list = core.scan_or_load(source)
    target_list = core.scan_or_load(target)
    patch_instructions = core.make_patch_instructions(source_list, target_list)

    print_json(patch_instructions)
    if out:
        dump_json(patch_instructions, out)

    if make_data:
        # implies direct access to source data
        # create patch data folder
        dump_json(source_list, os.path.join(data, "source.json"))
        dump_json(target_list, os.path.join(data, "target.json"))
        dump_json(patch_instructions, os.path.join(data, "patch.json"))
        core.copy_list(source, os.path.join(data, "files"), patch_instructions["copy"])


    # determine data directories
    source_dir = os.path.join(data, "files") if data else source
    target_dir = target

    # check patch data
    if data and not make_data:
        # make sure patch was created for our version of the data
        if not core.dir_content_same(target_dir, os.path.join(data, "target.json")):
            print("ERROR: target dir has changed after creating the patch")
            sys.exit(1)

        # make sure all necessary file for patching are available
        if not core.all_files_exist(source_dir, patch_instructions["copy"]):
            print("ERROR: files missing from data folder")
            sys.exit(1)

        print("data folder verified, ready for patching" + "with option '-p'" if not patch else "")


    # patch the target dir
    if patch:
        # check if both are actually dirs
        for dir in (source_dir, target_dir):
            if not os.path.isdir(dir):
                print("ERROR: not a directory, cannot patch: {}".format(dir))
                sys.exit(1)

        # patch
        patch(source_dir, target_dir, patch_instructions)

        # verify 
        if not core.dir_content_same(source_list, target_dir):
            print("ERROR: target dir does not match source after patching")
            sys.exit(1)
        else:
            print("patched and verified")


if __name__ == '__main__':  
    args = parse_args()
    pool = Pool()

    if not args.secondary:
        # only one dir given
        if args.data: 
            # args primary is target dir
            # get source info from data dir
            # no direct access to source files
            # patching from data dir is possible
            dual_dir_mode(
                source = os.path.join(args.data, "source.json"),
                target = args.primary,
                out = args.out,
                data = args.data,
                make_data = False,
                patch = args.patch,
                verbose = args.verbose
            )
        else:
            # scan dir
            single_dir_mode(args.primary, args.out, args.verbose)
    else:
        # args primary is actual source
        # args secondary might be either scan or actual target
        # direct patching and creation of data dir is possible
        dual_dir_mode(
            source = args.primary,
            target = args.secondary,
            out = args.out,
            data = args.data,
            make_data = bool(args.data),
            patch = args.patch,
            verbose = args.verbose
        )
