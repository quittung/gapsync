import os, shutil
import unittest
import filecmp
import subprocess

from gapsync.code.cli_logic import parse_args, process_args

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

def prepare_test():
    set_cwd()
    reset_dir()    

def dirs_identical(dir1, dir2):
    c = filecmp.dircmp(dir1, dir2)
    return len(c.left_only) == 0 and len(c.right_only) == 0 and len(c.diff_files) == 0


class TestIntegration(unittest.TestCase):
    def test_require_args(self):
        with self.assertRaises(SystemExit) as cm:
            parse_args([])
        
        self.assertEqual(cm.exception.code, 2)

    def test_sync_airgap_cli(self):
        """test sync with cli"""
        prepare_test()
        path_out = os.path.join(tmp_dir, "target.json")
        path_data = os.path.join(tmp_dir, "data")

        # step 1
        subprocess.call(["python3", "../gapsync", os.path.join(tmp_dir, "tgt"), "-o", path_out])
        self.assertTrue(filecmp.cmp(path_out, os.path.join("data/output", "target.json")), "scan output should match reference data")

        # step 2
        subprocess.call(["python3", "../gapsync", os.path.join(tmp_dir, "src"), path_out, "-d", path_data])
        self.assertTrue(dirs_identical(path_data, os.path.join("data/output", "data")), "data folder should match reference data")

        # step 3
        subprocess.call(["python3", "../gapsync", os.path.join(tmp_dir, "tgt"), "-d", path_data, "-p"])
        self.assertTrue(dirs_identical(os.path.join(tmp_dir, "src"), os.path.join(tmp_dir, "tgt")), "source and target should be identical")

    def test_sync_airgap(self):
        """test sync with imported functions for easier debugging"""
        prepare_test()
        path_out = os.path.join(tmp_dir, "target.json")
        path_data = os.path.join(tmp_dir, "data")

        # step 1
        process_args(parse_args([os.path.join(tmp_dir, "tgt"), "-o", path_out]))
        self.assertTrue(filecmp.cmp(path_out, os.path.join("data/output", "target.json")), "scan output should match reference data")

        # step 2
        process_args(parse_args([os.path.join(tmp_dir, "src"), path_out, "-d", path_data]))
        self.assertTrue(dirs_identical(path_data, os.path.join("data/output", "data")), "data folder should match reference data")

        # step 3
        process_args(parse_args([os.path.join(tmp_dir, "tgt"), "-d", path_data, "-p"]))
        self.assertTrue(dirs_identical(os.path.join(tmp_dir, "src"), os.path.join(tmp_dir, "tgt")), "source and target should be identical")

    def test_sync_direct(self):
        prepare_test()

        process_args(parse_args([os.path.join(tmp_dir, "src"), os.path.join(tmp_dir, "tgt"), "-p"]))
        self.assertTrue(dirs_identical(os.path.join(tmp_dir, "src"), os.path.join(tmp_dir, "tgt")), "source and target should be identical")



if __name__ == '__main__':  
    unittest.main()

    