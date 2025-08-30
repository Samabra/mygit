#!/usr/bin/env python3

import os
import sys
import re
import json

# Standard existing repo check
mygit = ".mygit"
if not os.path.isdir(mygit):
    print("mygit-show: error: mygit repository directory .mygit not found", file=sys.stderr)
    sys.exit(1)


# Define how the command should go
show_file_pattern = re.compile(r'^[^:]*:[^:]+$')
if len(sys.argv) != 2 or not show_file_pattern.fullmatch(sys.argv[1]):
    print("usage: mygit-show <commit>:<filename>", file=sys.stderr)
    sys.exit(1)

arg = sys.argv[1]
commit = arg.split(":")[0]
filename = arg.split(":")[1]

commit_pattern = re.compile(r'[0-9]*')

# Check for invalid commits
if not commit_pattern.fullmatch(commit):
    print(f"mygit-show: error: unknown commit '{commit}'", file=sys.stderr)
    sys.exit(1)


# Get the specified commit file
commit_file = None
if commit != "":
    commit_file = os.path.join(mygit, "objects", f"{commit}.json")
    if not os.path.exists(commit_file):
        print(f"mygit-show: error: unknown commit '{commit}'", file=sys.stderr)
        sys.exit(1)

file_pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')
if not file_pattern.fullmatch(filename):
    print(f"mygit-show: error: invalid filename '{filename}", file=sys.stderr)
    sys.exit(1)

# If no commit specified, we show the file of the most previous commit as per the index 
if commit == "":
    index_file = os.path.join(mygit, "index")
    with open(index_file, "r") as file:
        index_entries = [line.strip().split(" ") for line in file if line.strip()]
    index_map = {fname: sha1 for fname, sha1 in index_entries}

    if filename not in index_map:
        print(f"mygit-show: error: '{filename}' not found in index", file=sys.stderr)
        sys.exit(1)
    
    blob_hash = index_map[filename]
    blob_path = os.path.join(mygit, "objects", "blobs", blob_hash)

    with open(blob_path, "r") as blob_file:
        print(blob_file.read(), end="")
    sys.exit(0)

# Open commit file and get all files listed in commit file
with open(commit_file, "r") as file:
    commit_data = json.load(file)

map_file = commit_data.get("files", {})
if filename not in map_file:
    print(f"mygit-show: error: '{filename}' not found in commit {commit}", file=sys.stderr)
    sys.exit(1)

blob_hash = map_file[filename]

# If the blob doesn't exist (which is unlikely) then just exit
blob_path = os.path.join(mygit, "objects", "blobs", blob_hash)
if not os.path.exists(blob_path):
    sys.exit(1)

# Print file stored in the blobs directory
with open(blob_path, "r") as blob_file:
    print(blob_file.read(), end="")









