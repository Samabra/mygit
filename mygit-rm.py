#!/usr/bin/env python3
import os
import sys
import re
import json
from helper import file_sha1sum

USAGE_MESSAGE = "usage: mygit-rm [--force] [--cached] <filenames>"

# Check if .mygit folder exists
mygit = ".mygit"
index_file = os.path.join(mygit, "index")
objects_dir = os.path.join(mygit, "objects")
blobs_dir = ".mygit/objects/blobs"

if not os.path.isdir(mygit):
    print("mygit-rm: error: mygit repository directory .mygit not found", file=sys.stderr)
    sys.exit(1)

args = sys.argv[1:]

valid_file = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')
flags_allowed = ["--", "--force", "--cached"]
flag_check = re.compile(r'^[-]+[^\s]+$')

if not args:
    print(USAGE_MESSAGE, file=sys.stderr)
    sys.exit(1)

# Check for any invalid options, including misspelt ones
for arg in args:
    if flag_check.fullmatch(arg) and arg not in flags_allowed:
        print(USAGE_MESSAGE, file=sys.stderr)
        sys.exit(1)

force = False
cached = False
file_seen = False
flag_seen = False

# Check for any options that are set
if "--force" in args:
    force = True
if "--cached" in args:
    cached = True

filenames = []

# We look at the "--" that indicates that the command line argument
# will have to be given file arguments after it.
if "--" in args:

    # Case for no flags set
    # Simply will be filenames
    if not cached and not force:
        arg_without_options = [arg for arg in args if arg != "--"]
        filenames = [f for f in arg_without_options if f.strip()]
        if not filenames:
            print(USAGE_MESSAG, file=sys.stderr)
            sys.exit(1)
        for file in filenames:
            filenames.append(file)
    
    # If flags are set then we deal with the arguments around "--"
    else:
        idx = args.index("--")
        before = args[:idx]
        after = args[idx + 1:]

        # No arguments before and after "--" -> invalid case
        if not before and not after:
            print(USAGE_MESSAGE, file=sys.stderr)
            sys.exit(1)
        
        # Basically what we are doing is checking that when
        # there is a "--" in our args is that
        # 1) Is there at least one filename before the "--"
        # 2) Are there only filenames after the "--"
        # 3) Are filenames named consecutively without being interspersed with flags
        for count, argument in enumerate(before):
            if argument in flags_allowed:
                if argument == before[-1]:
                    print(USAGE_MESSAGE, file=sys.stderr)
                    sys.exit(1)
                flag_seen = True
            else:
                if flag_seen and file_seen:
                    if before[count - 1] in flags_allowed:
                        print(USAGE_MESSAGE, file=sys.stderr)
                        sys.exit(1)
                filenames.append(argument)
                file_seen = True
        
        for file in after:
            filenames.append(file)
else:
    # Ensure filenames are named consecutively
    # So -flag filename -flag filename is an invalid case
    for count, argument in enumerate(args):
        if argument in flags_allowed:
            flag_seen = True
        else:
            if flag_seen and file_seen:
                if args[count - 1] in flags_allowed:
                    print(USAGE_MESSAGE, file=sys.stderr)
                    sys.exit(1)
            filenames.append(argument)
            file_seen = True


# Retrieve index file
if not os.path.exists(index_file):
    open(index_file, "w").close()

with open(index_file, "r") as file:
    index_entries = [line.strip().split(None, 1) for line in file if line.strip()]
index_map = {fname: sha1 for fname, sha1 in index_entries}


# Get current branch

head_file = os.path.join(mygit, "HEAD")
with open(head_file, "r") as file:
    head_content = file.read().strip()

branch_path = head_content.replace("ref: ", "")
branch_file = os.path.join(".mygit", branch_path)

# Get the previous commit
last_commit = None
previous_commit_files = {}
if os.path.exists(branch_file):
    with open(branch_file, "r") as file:
        last_commit = file.read().strip()
    if last_commit:
        commit_file = os.path.join(objects_dir, f"{last_commit}.json")
        if os.path.exists(commit_file):
            with open(commit_file, "r") as file:
                previous_commit_files = json.load(file).get("files", {})


# Check for any files not in the repository 
# Any files not in the repository stops us from removing any files.
for file in filenames:
    if file not in index_map:
        print(f"mygit-rm: error: '{file}' is not in the mygit repository", file=sys.stderr)
        sys.exit(1)

# Check if working file != file in repository
# If index != working file and index != file in repository (according to last commit)
# Or if there are changes that still need to be committed
# If --cached, then we only care about if index != working file and index != repo (according to last commit)
# If --force, ignore any warnings and just remove anyways
for file in filenames:
    if not valid_file.fullmatch(file):
        print(f"mygit-rm: error: invalid filename '{file}'", file=sys.stderr)
        sys.exit(1)
    sha1 = index_map[file]
    working_exists = os.path.exists(file)
    working_hash = file_sha1sum(file) if working_exists else None

    if force:
        if cached:
            del index_map[file]
        else:
            del index_map[file]
            if working_exists:
                os.remove(file)
        continue

    if cached:
        if working_exists and working_hash != sha1:
            if last_commit == "" or file not in previous_commit_files or previous_commit_files[file] != sha1:
                print(f"mygit-rm: error: '{file}' in index is different to both the working file and the repository", file=sys.stderr)
                sys.exit(1)
        del index_map[file]
        continue

    if working_exists and working_hash != sha1:
        if last_commit == "" or file not in previous_commit_files or previous_commit_files[file] != sha1:
            print(f"mygit-rm: error: '{file}' in index is different to both the working file and the repository", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"mygit-rm: error: '{file}' in the repository is different to the working file", file=sys.stderr)
            sys.exit(1)
    
    if last_commit == "" or file not in previous_commit_files or previous_commit_files[file] != sha1:
        print(f"mygit-rm: error: '{file}' has staged changes in the index", file=sys.stderr)
        sys.exit(1)
    del index_map[file]
    if working_exists:
        os.remove(file)

with open(index_file, "w") as file:
    for fname, sha1 in index_map.items():
        file.write(f"{fname} {sha1}\n")
   
    



    
    








        









