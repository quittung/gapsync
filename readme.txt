this is for syncing folders you don't have simultaneous access to

to do that it
- scans the target folder

- scans the source folder
- compares the files
- spits out a patch list
- moves the necessary files to directory of the users choice

- applies that patch to the target directory

as the source and target cannot be accessed at the same time, these three blocks will have to be worked through individually

these are the relevant arguments
- source dir or file list
- target dir or file list
- work dir for patch and data
- optional output path 


if only one dir is given, it will scan
if an output path is given, it will export that scan

if two dirs are given, it will compare the directories
if an output path is given, it will export the patch instructions
if a data path is given, it will drop the patch instructions and the necessary files there

if only one dir is given, but a data path is given, it will load the patch instructions

if a target dir is given, patch instructions are loaded and the patch argument is passed, it will apply the patch



data folder
patch.json - patch instructions
target.json - file list for target
files folder - files that need to be copied



examples: 
1. scanning the target dir, exporting results to file:
msync *target_dir* -o *scan_output_path*

2. prepare patch using scan:
msync *source_dir* *path_to_target_scan* -d *data_dir*

3. patch target folder with prepared data folder from 2
msync *target_dir* -d *data_dir* -p

alternative when both folders accessible:
msync *source_dir* *target_dir* -p