# gapsync
Sync directories you cannot access at the same time

## What is this good for?
You have two directories you want to synchronize, but
 - sending the entire folder is impractical
 - you cannot access both folders at the same time

Maybe you updated a few files in a 30 Gb directory and you want to bring your friend's version up to date without resending the entire thing.
As long as you can run a standard python3 interpreter at both ends, you're good to go.

## How does it work?
Gapsync scans the target directory locally and creates a summary of the files. This summary is then locally compared to the source directry. Patch data is compiled and only necessary files are sent to the target system. Finally, the patch is applied to the target system.

### Step 1 - Scanning the target directory
Ask your friend to scan the target directory:
```
python3 gapsync *target_dir* -o target.json
```
This creates a list of files and their sha256 hashes and saves it as `target.json` in the current working directory. The name of the output file is not important. Here is a sample output:
```
{
    "1.txt": "cb81c5cc33482338f6ff3c088afb313686d290d6f5feeb05f5b5cc906cb938eb",
    "2.txt": "4958648a409351122db1c235a363d4ae36d2f6d124904e051dce3206c643d43f",
    "3.txt": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "subfolder/A.txt": "f2d20f255b6df160d8b461db0315e3b2c9024f45a3094b217ad60d9381b35fa0",
    "subfolder/B.txt": "75e2600644a2bf05f9a81e691d1e2b0875d8325f3e672056b1c3e9e61029dce9"
}
```
Your friend needs to send `target.json` to you for the next step.

### Step 2 - Comparison and patch preparation
Compare the target directory's state to your master copy - the source directy:
```
python3 gapsync *source_dir* target.json -d *data_dir*
```
This command automatically compiles the patch instructions and the new or changed files in the `data_dir` directory. 
The instructions will have this format:
```
{
    "copy": [
        "1.txt",
        "3.txt",
        "subfolder/B.txt"
    ],
    "delete": [
        "4.txt",
        "foo/Z.txt"
    ]
}
```
Don't worry, you won't have to apply it manually.
Send the data directory over to your friend.

### Step 3 - Applying the patch
In this final step your friend will have to run the following command:
```
python3 gapsync *target_dir* -d *data_dir* -p
```
After some checks, the patch you calculated will be applied to the target directory.
If your friend wants to do a dry run first, without changing any files, just omit the `-p` flag.

## Arguments & Usage
Call the script using `python3 *path_to_gapsync_folder_or_executable* *args*`. If you use the executable on Unix, you can run it directly: `*path_to_gapsync* *args*`.

Gapsync expects one or two paths as positional arguments: `gapsync *primary* [*secondary*]`. Either path can be a directory or a previously exported directory scan.

There are three basic modes the script can run in:
 - Scan - one path: `gapsync *dir_to_scan* *args*`
   - `-o *out_path*`, optional - output scan as json file
   - `-v`, optional - verbose mode, get update for every file interaction in real time
 - Compare - two paths: `gapsync *source_dir* *target_dir* *args*`
   - `-o *out_path*`, optional - to output patch instructions as json file
   - `-d *data_dir*`, optional - to compile all necessary file for patching in a directory
   - `-p`, optional - patch immediately, only useful if both paths are actual directories
   - `-v`, optional - verbose mode, get update for every file interaction in real time
 - Patch - one path and data directory: `gapsync *target_dir* -d *data_dir* *args*`
   - `-d *data_dir*`, mandatory - source of patch data
   - `-p`, optional - apply patch to target directory
   - `-v`, optional - verbose mode, get update for every file interaction in real time