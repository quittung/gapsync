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
python3 gapsync scan <target_dir> -o target.json
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
python3 gapsync diff <source_dir> target.json -d <data_dir>
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
python3 gapsync patch <data_dir> <target_dir>
```
After some checks, the patch you calculated will be applied to the target directory.
If your friend wants to do a dry run first, without changing any files, just add the `-t` flag.

## Arguments
Call the script using `python3 <path_to_gapsync> <subcommand> <args>`. If you use the executable on Unix, you can run omit the `python3` prefix.

### Top level flags
 - `-h` shows general help and quits
 - `--version` shows version and quits
 - `--license` shows license and quits

### scan
```python3 gapsync scan [<dir>] [-o OUT]```
 - Scans a directory and generates a list of files and their sha256 hashes
 - Omitting `<dir>` scans current workding directory
 - `-o` saves the list as a file
 - Also available as `python3 gapsync scan [<dir>] [-o OUT]` 

### diff
```python3 gapsync diff <source> <target>  [-o OUT] [-d DATA]```
 - Compares two directories and generates patch instructions
 - `<source>` and `<target>` can either be directories or scans of directories
 - `-o` saves the list as a file
 - `-d` compiles necessary files into a data folder, requires `<source>` to be a directory

### patch
```python3 gapsync patch <data> <target> [-t]```
 - Patches a directory using instructions and files from a data folder
 - `-t` can be used to perform a dry run without changing any files

### Common subcommand flags
 - `-h` show help
 - `-s` single threaded mode, may reduce random reads during scanning
 - `-v` increase output verbosity, especially more frequent status updates


## License
This script is licensed under the MIT license, so you can do pretty much anything you want. You don't even need to include the license when redistributing, because it is already baked into the executable (`gapsync --license`). The software is provided without warranty. See the `LICENSE` file for details.
