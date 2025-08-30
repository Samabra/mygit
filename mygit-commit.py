#!/usr/bin/env python3


import sys
import shutil
import os
from datetime import datetime
import json
from helper import file_sha1sum, read_seq, next_commit_id, bump_seq

mygit = ".mygit"
index_file = ".mygit/index"
objects_dir = ".mygit/objects"
seq_file = os.path.join(mygit, "SEQ")

if not os.path.isdir(mygit):
    print("mygit-commit: error: mygit repository directory .mygit not found")
    sys.exit(1)


args = sys.argv[1:]

if not (len(args) >= 2 and args[-2] == "-m"):
    print("usage: mygit-commit [-a] -m commit-message", file=sys.stderr)
    sys.exit(1)


if args[0] == "-m":
    commit_message = " ".join(args[1:])
elif len(args) >= 3 and args[0] == "-a" and args[1] == "-m":
    commit_message = " ".join(args[2:])
else:
    print("usage: mygit-commit [-a] -m commit-message", file=sys.stderr)
    sys.exit(1)

if commit_message.strip() == "":
    print("usage: mygit-commit [-a] -m commit-message", file=sys.stderr)
    sys.exit(1)

a_flag = args[0] == "-a"


# Load the index file
if not os.path.exists(index_file):
    open(index_file, "w").close()

with open(index_file, "r") as file:
    index_entries = [line.strip().split(None, 1) for line in file if line.strip()]

index_map = {filename: sha1 for filename, sha1 in index_entries} if index_entries else {}


# If a flag, then update index with all files in working directory
# including all their changes
if a_flag:
    for filename in list(index_map.keys()):
        if os.path.isfile(filename):
            index_map[filename] = file_sha1sum(filename)
        else:
            del index_map[filename]
    with open(index_file, "w") as file:
        for fname, sha1 in index_map.items():
            file.write(f"{fname} {sha1}\n")


current_files = dict(index_map)

# Get current branch
head_content = None
with open(".mygit/HEAD", "r") as head_file:
    head_content = head_file.read().strip()

branch_path = head_content.replace("ref: ", "")
branch_file = os.path.join(".mygit", branch_path)

changed = False

# Read the commit that this branch is pointing to
with open(branch_file, 'r') as file:
    last_commit = file.read().strip()

# Check for any staged changes
parent = int(last_commit) if last_commit else None
if parent is None:
    if current_files:
        changed = True
else:
    previous_commit = os.path.join(objects_dir, f"{parent}.json")
    with open(previous_commit, 'r') as parent_commit:
        parent_data = json.load(parent_commit)
    previous_commit_files = parent_data.get("files", {})
    if current_files != previous_commit_files:
        changed = True

# If no changes detected, don't commit
if not changed:
    print("nothing to commit")
    sys.exit(1)

# Get next commit number
commit_num = next_commit_id(seq_file)

# Make a new blob file for any file that is changed
# Copy file content into that blob content
blobs_dir = os.path.join(objects_dir, "blobs")
os.makedirs(blobs_dir, exist_ok=True)

for file, sha1 in current_files.items():
    blob_path = os.path.join(blobs_dir, sha1)
    if not os.path.exists(blob_path) and os.path.exists(file):
        shutil.copy2(file, blob_path)

# Timestamp for fun
timestamp = datetime.now().isoformat(timespec='seconds')

# Commit files stored as JSON file, which contains all the essential information
# about a commit
new_commit = {
    "commit_num": commit_num,
    "parent": None if last_commit == "" else parent,
    "message": commit_message,
    "timestamp": timestamp,
    "files": current_files
}

# Create new commit JSON file
commit_path = os.path.join(mygit, "objects", f"{commit_num}.json")
with open(commit_path, "w") as file:
    json.dump(new_commit, file, indent=4)


# Update branch pointer
with open(branch_file, "w") as file:
    file.write(str(commit_num))

# Change number in SEQ file
bump_seq(seq_file, commit_num)

print(f"Committed as commit {commit_num}")








