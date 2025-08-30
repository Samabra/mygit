#!/usr/bin/env python3

import os
import sys
import shutil
import re
from helper import file_sha1sum


# Checking if filenames have been input
if len(sys.argv) < 2:
    print("usage: mygit-add <filenames>", file=sys.stderr)
    sys.exit(1)

# Regex for valid file
file_pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')
mygit = ".mygit"
index_file = os.path.join(mygit, "index")
blobs_dir = os.path.join(mygit, "objects", "blobs")

# Check if repository exists
if not os.path.isdir(mygit):
    print("mygit-add: error: mygit repository directory .mygit not found", file=sys.stderr)
    sys.exit(1)

# Load files and the hash of each file in a dict
index_data = {}
if os.path.exists(index_file):
    with open(index_file, "r") as file:
        for line in file:
            name, sha1 = line.strip().split()
            index_data[name] = sha1


for filename in sys.argv[1:]:
    if not file_pattern.fullmatch(filename):
        print(f"mygit-add: error: invalid filename '{filename}'", file=sys.stderr)
        sys.exit(1)
    
    # Remove file if it doesn't exist in working directory
    if not os.path.exists(filename):
        if filename in index_data:
            del index_data[filename]
        else:
            print(f"mygit-add: error: can not open '{filename}'", file=sys.stderr)
            sys.exit(1)
    # Compute the sha1sum of the file and store it in the dict for now
    # And add blob file with the file content copied into the blob file
    else:
        sha1 = file_sha1sum(filename)
        index_data[filename] = sha1
        blob_path = os.path.join(blobs_dir, sha1)
        if not os.path.exists(blob_path):
            shutil.copy2(filename, blob_path)


# Update the index file with the filename and the sha1sum of the filename
with open(index_file, "w") as file:
    for name, sha1 in index_data.items():
        file.write(f"{name} {sha1}\n")
