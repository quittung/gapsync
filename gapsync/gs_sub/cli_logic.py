import argparse, os, sys
import subprocess
from multiprocessing.pool import Pool
import pkgutil

from .core import *
from .serialize import dump_json, print_json

def load_str(file: str):
    data = pkgutil.get_data(__package__, file)
    return data.decode("utf-8") 

def get_version():
    try:
        return load_str("cli_version.txt")
    except:
        if shutil.which("git") != None:
            return subprocess.check_output(["git", "describe", "--tags"]).decode("utf-8").strip() + "-dev"
        else:
            return "unknown"

def parse_args(args: list = None):
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument("primary", help="primary path")
    parser.add_argument("secondary", nargs="?", help="secondary path")
    parser.add_argument("-o", "--out", help="output path for json files (scan or patch instructions)")
    parser.add_argument("-d", "--data", help="data directory")
    parser.add_argument("-p", "--patch", action='store_true', help="actually modify the target directory")
    parser.add_argument("-s", "--single_threaded", action="store_true", help="use a single thread for scanning only")
    parser.add_argument("-v", "--verbose", action='store_true')
    
    parser.add_argument("--version", action="version", version=get_version())

    parser.description = "tool for synchronizing two directories across different systems without simultaneous access\nworks with airgapped systems and only sends changed files"
    parser.epilog = load_str("cli_help.txt") + load_str("cli_license.txt")

    args_parsed = parser.parse_args(args) if args else parser.parse_args()
    return args_parsed

def single_dir_mode(dir: str, out: str, verbose: bool, single_threaded: bool):
    """this mode only supports scanning a single directory and outputting the result"""
    pool = None if single_threaded else Pool()
    file_list = scan_or_load(dir, pool, verbose)
    if pool: pool.close()

    print_json(file_list)
    if out:
        dump_json(file_list, out)

def dual_dir_mode(source: str, target: str, out: str, data: str, make_data: bool, patch: bool, verbose: bool, single_threaded: bool):
    pool = None if single_threaded else Pool()
    source_list = scan_or_load(source, pool, verbose)
    target_list = scan_or_load(target, pool, verbose)
    patch_instructions = make_patch_instructions(source_list, target_list)

    print_json(patch_instructions)
    if out:
        dump_json(patch_instructions, out)

    if make_data:
        # implies direct access to source data
        # create patch data folder
        dump_json(source_list, os.path.join(data, "source.json"))
        dump_json(target_list, os.path.join(data, "target.json"))
        dump_json(patch_instructions, os.path.join(data, "patch.json"))
        copy_list(source, os.path.join(data, "files"), patch_instructions["copy"])


    # determine data directories
    source_dir = os.path.join(data, "files") if data else source
    target_dir = target

    # check patch data
    if data and not make_data:
        # make sure patch was created for our version of the data
        if not dir_content_same(target_dir, os.path.join(data, "target.json"), pool, verbose):
            print("ERROR: target dir has changed after creating the patch")
            sys.exit(1)

        # make sure all necessary file for patching are available
        if not all_files_exist(source_dir, patch_instructions["copy"]):
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
        apply_patch(source_dir, target_dir, patch_instructions, verbose)

        # verify 
        if not dir_content_same(source_list, target_dir, pool, verbose):
            print("ERROR: target dir does not match source after patching")
            sys.exit(1)
        else:
            print("patched and verified")
    
    if pool: pool.close()

def process_args(args: argparse.Namespace):
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
                verbose = args.verbose,
                single_threaded = args.single_threaded
            )
        else:
            # scan dir
            single_dir_mode(args.primary, args.out, args.verbose, single_threaded = args.single_threaded)
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
            verbose = args.verbose,
            single_threaded = args.single_threaded
        )