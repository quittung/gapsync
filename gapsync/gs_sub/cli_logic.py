import argparse, os, sys, shutil
import subprocess
from multiprocessing.pool import Pool
import pkgutil

from . import core, serialize

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

class GapsyncParser(object):
    def __init__(self, args_raw: list) -> None:
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
        
        parser.description = "tool for synchronizing two directories across different systems without simultaneous access"
        parser.epilog = load_str("cli_help.txt")

        parser.add_argument('command', nargs='?', default=".", help='subcommand to run')
        parser.add_argument("--version", action="version", version=get_version())
        parser.add_argument("--license", action="version", version=load_str("cli_license.txt"), help="show license and exit")
        
        args = parser.parse_args(args_raw[1:2])
        # handle unrecognized commands
        if not hasattr(self, args.command):
            # handle basic mode -> scan (current) directory
            if os.path.exists(args.command):
                args_raw.insert(1, "scan")
                args = parser.parse_args(args_raw[1:2])
            else:
                print('unrecognized command')
                parser.print_help()
                exit(1)

        # call subcommand
        getattr(self, args.command)(args_raw[2:])
    

    def scan(self, args_raw):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)

        parser.description = "scans a directory and calculates the sha256 hash of every file"

        parser.add_argument("dir", nargs="?", default=".", help="directory to be scanned")
        parser.add_argument("-o", "--out", help="export scan as json in this path")
        parser.add_argument("-s", "--single_threaded", action="store_true", help="limit to single thread")
        parser.add_argument("-v", "--verbose", action='store_true', help="get immediate output after each hash is calculated")

        args = parser.parse_args(args_raw)

        # start scan
        pool = None if args.single_threaded else Pool()
        file_list = core.scan_or_load(args.dir, pool, args.verbose)
        if pool: pool.close()

        serialize.print_json(file_list)
        if args.out:
            serialize.dump_json(file_list, args.out)


    def diff(self, args_raw):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)

        parser.description = "compares two directories (or their scans) and optionally compiles data for patching"
    
        parser.add_argument("source", help="source path or scan")
        parser.add_argument("target", help="target path or scan")
        parser.add_argument("-o", "--out", help="export comparison as json in this path")
        parser.add_argument("-d", "--data", help="create data directory in this path")
        parser.add_argument("-s", "--single_threaded", action="store_true", help="limit to single thread")
        parser.add_argument("-v", "--verbose", action='count', default=0, help="get more output")

        args = parser.parse_args(args_raw)

        # start comparison
        pool = None if args.single_threaded else Pool()

        if args.verbose: print("getting file scan for source directory")
        source_list = core.scan_or_load(args.source, pool, args.verbose > 1)

        if args.verbose: print("getting file scan for target directory")
        target_list = core.scan_or_load(args.target, pool, args.verbose > 1)

        if pool: pool.close()

        if args.verbose: print("comparing source and target")
        patch_instructions = core.make_patch_instructions(source_list, target_list)

        serialize.print_json(patch_instructions)
        if args.out:
            serialize.dump_json(patch_instructions, args.out)

        if args.data:
            if args.verbose: print("compiling patch data")
            if not os.path.isdir(args.source):
                print("ERROR: data path is not a directory")
                exit(1)
                
            # create patch data folder
            serialize.dump_json(source_list, os.path.join(args.data, "source.json"))
            serialize.dump_json(target_list, os.path.join(args.data, "target.json"))
            serialize.dump_json(patch_instructions, os.path.join(args.data, "patch.json"))
            core.copy_list(args.source, os.path.join(args.data, "files"), patch_instructions["copy"], args.verbose > 1)


    def patch(self, args_raw):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
        
        parser.description = "patches a directory using the data compiled by diff subcommand"
    
        parser.add_argument("data", help="data directory")
        parser.add_argument("target", help="target directory")
        parser.add_argument("-t", "--test_only", action='store_true', help="don't modify the target directory")
        parser.add_argument("-s", "--single_threaded", action="store_true", help="limit to single thread")
        parser.add_argument("-v", "--verbose", action='store_true', help="get immediate output after each file operation")

        args = parser.parse_args(args_raw)

        # start patch
        print("processing data")
        data_files = os.path.join(args.data, "files")

        # make sure bot paths are actually directories
        for dir in (data_files, args.target):
            if not os.path.isdir(dir):
                print("ERROR: {} is no directory, cannot patch".format(dir))
                sys.exit(1)

        source_list = core.scan_or_load(os.path.join(args.data, "source.json"), None, args.verbose)
        target_list = core.scan_or_load(os.path.join(args.data, "target.json"), None, args.verbose)
        patch_instructions = core.make_patch_instructions(source_list, target_list)

        print("checking patch files")
        pool = None if args.single_threaded else Pool()

        # make sure patch was created for our version of the data
        if not core.dir_content_same(args.target, target_list, pool, args.verbose):
            print("ERROR: target dir has changed after creating the patch")
            if pool: pool.close()
            sys.exit(1)

        # make sure all necessary file for patching are available
        if not core.all_files_exist(data_files, patch_instructions["copy"]):
            print("ERROR: files missing from data folder")
            if pool: pool.close()
            sys.exit(1)

        # move on to copying and removing files if requested
        print("patch data verified")
        if not args.test_only:
            # patch
            core.apply_patch(data_files, args.target, patch_instructions, args.verbose)

            # verify 
            if not core.dir_content_same(source_list, args.target, pool, args.verbose):
                print("ERROR: target dir does not match source after patching")
                if pool: pool.close()
                sys.exit(1)
            else:
                print("patched and verified")
        
        if pool: pool.close()
