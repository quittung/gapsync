import os, shutil
import unittest
import filecmp
import subprocess

from gapsync.gs_sub import cli_logic

tmp_dir = "data_tmp"

# change working directory
def set_cwd():
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    dname = os.path.join(dname, "test")
    os.chdir(dname)

# make copy of test data
def reset_dir():
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    shutil.copytree("data/base", tmp_dir)

class TestVarsFullProcess(object):
    def __init__(self, prefix = ["gapsync"], suffix = []):
        self.path_src = os.path.join(tmp_dir, "src")
        self.path_tgt = os.path.join(tmp_dir, "tgt")
        self.path_out = os.path.join(tmp_dir, "target.json")
        self.path_data = os.path.join(tmp_dir, "data")

        commands = [
            ["scan", self.path_tgt, "-o", self.path_out],
            ["diff", self.path_src, self.path_out, "-d", self.path_data],
            ["patch", self.path_data, self.path_tgt]
        ]

        self.commands = [prefix + command + suffix for command in commands]


def prepare_test():
    set_cwd()
    reset_dir()    

def dirs_identical(dir1, dir2):
    c = filecmp.dircmp(dir1, dir2)
    return len(c.left_only) == 0 and len(c.right_only) == 0 and len(c.diff_files) == 0


class TestIntegration(unittest.TestCase):
    def run_full_sync(self, test_vars, execution_method = cli_logic.GapsyncParser):
        prepare_test()

        # step 1
        execution_method(test_vars.commands[0])
        self.assertTrue(filecmp.cmp(test_vars.path_out, os.path.join("data/output", "target.json")), "scan output should match reference data")

        # step 2
        execution_method(test_vars.commands[1])
        self.assertTrue(dirs_identical(test_vars.path_data, os.path.join("data/output", "data")), "data folder should match reference data")

        # step 3
        execution_method(test_vars.commands[2])
        self.assertTrue(dirs_identical(test_vars.path_src, test_vars.path_tgt), "source and target should be identical")


    def test_sync_imported(self):
        """test sync with imported functions for easier debugging"""
        self.run_full_sync(TestVarsFullProcess())

        
    def test_sync_imported_singlethreaded(self):
        """test sync with imported functions for easier debugging"""
        self.run_full_sync(TestVarsFullProcess(suffix=["-s"]))


    def test_sync_build(self):
        """test sync process with built executable
        FAILS IN DEBUG BUT RUNS FINE AS NORMAL TEST"""

        # build app
        set_cwd()
        os.chdir("..")
        subprocess.call(["python3", "build.py"])
        os.chdir("test")

        self.run_full_sync(TestVarsFullProcess(prefix=["python3", "../dist/gapsync"]), subprocess.call)


if __name__ == '__main__':  
    unittest.main()

    