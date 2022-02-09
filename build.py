import os
import subprocess
import shutil
import zipapp

path_source = "gapsync"
path_executable = "dist/gapsync"
path_interpreter = "/usr/bin/python3"
path_version = "gapsync/gs_sub/cli_version.txt"

if shutil.which("git") != None:
    version = subprocess.check_output(["git", "describe", "--tags"]).decode("utf-8").strip()
    status = subprocess.check_output(["git", "status", "-s"]).decode("utf-8").strip()

    if not status == "":
        version += "-dirty"

    print("detected version {}".format(version))
    with open(path_version, 'w') as fobj:
        fobj.write(version)

dir_executable = os.path.dirname(path_executable)
if not os.path.exists(dir_executable):
    os.makedirs(dir_executable)
    print("created dist folder")
    
zipapp.create_archive(path_source, path_executable, path_interpreter, compressed=True)
print("created archive")

if os.path.exists(path_version):
    os.remove(path_version)