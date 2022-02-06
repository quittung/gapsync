import os, shutil
import subprocess
import unittest
import filecmp

from gapsync.cli_logic import parse_args, process_args

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



class TestIntegration(unittest.TestCase):
    def test_require_args(self):
        with self.assertRaises(SystemExit) as cm:
            parse_args([])
        
        self.assertEqual(cm.exception.code, 2)

    def test_scan_output(self):
        prepare_test()
        path_out = os.path.join(tmp_dir, "target.json")

        process_args(parse_args([os.path.join(tmp_dir, "tgt"), "-o", path_out]))
        self.assertTrue(filecmp.cmp(path_out, os.path.join("data/output", "target.json")))

if __name__ == '__main__':  
    unittest.main()

    