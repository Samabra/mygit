#!/usr/bin/env python3

import os
import sys
import json
import re
from helper import file_sha1sum

mygit = ".mygit"
index_file = os.path.join(mygit, "index")
objects_dir = os.path.join(mygit, "objects")

if not os.path.isdir(mygit):
    print("mygit-status: error: mygit repository directory .mygit not found", file=sys.stderr)
    sys.exit(1)

valid_file = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')

working_files = sorted(
    file for file in os.listdir('.')
    if os.path.isfile(file) and valid_file.fullmatch(file)
)

if not os.path.exists(index_file):
    open(index_file, "w").close()

with open(index_file, "r") as file:
    index_entries = [line.strip().split(None, 1) for line in file if line.strip()]

index_map = {filename: sha1 for filename, sha1 in index_entries} if index_entries else {}

head_file = os.path.join(mygit, "HEAD")
with open(head_file, "r") as file:
    head_content = file.read().strip()

branch_path = head_content.replace("ref: ", "")
branch_file = os.path.join(".mygit", branch_path)


previous_commit_files = {}
if os.path.exists(branch_file):
    with open(branch_file, "r") as file:
        last_commit = file.read().strip()
    if last_commit:
        commit_file = os.path.join(objects_dir, f"{last_commit}.json")
        if os.path.exists(commit_file):
            with open(commit_file, "r") as file:
                previous_commit_files = json.load(file).get("files", {})


# Create a sorted set that combines working files, files in index and files in commit
all_files = sorted(set(working_files) | set(index_map) | set(previous_commit_files))

for file in all_files:
    in_working = file in working_files
    in_index = file in index_map
    in_commit = file in previous_commit_files

    working_sha1 = file_sha1sum(file) if in_working else None
    index_sha1 = index_map.get(file)
    commit_sha1 = previous_commit_files.get(file)

    # If file not in commit
    if not previous_commit_files:
        if in_index and not in_working:
            print(f"{file} - added to index, file deleted")
        elif in_index and in_working:
            if working_sha1 == index_sha1:
                print(f"{file} - added to index")
            else:
                print(f"{file} - added to index, file changed")
        elif in_working and not in_index:
            print(f"{file} - untracked")
        continue
    
    # File is in the commit but has been deleted from index and working dir
    if not in_index and not in_working and in_commit:
        print(f"{file} - file deleted, deleted from index")
    # File in repository but not in index
    elif in_commit and not in_index:
        if in_working:
            print(f"{file} - deleted from index")
        else:
            print(f"{file} - file deleted, deleted from index")
    # Check for untracked file
    elif not in_index and in_working and not in_commit:
        print(f"{file} - untracked")
    
    # If file is in index
    elif in_index and not in_working:
        if not in_commit:
            print(f"{file} - added to index, file deleted")
        else:
            if index_sha1 == commit_sha1:
                print(f"{file} - file deleted")
            else:
                print(f"{file} - file deleted, changes staged for commit")
    # File in index and working dir
    elif in_index and in_working:
        if not in_commit:
            if working_sha1 == index_sha1:
                print(f"{file} - added to index")
            else:
                print(f"{file} - added to index, file changed")
        else:
            if working_sha1 == index_sha1 == commit_sha1:
                print(f"{file} - same as repo ")
            elif index_sha1 == commit_sha1 and working_sha1 != index_sha1:
                print(f"{file} - file changed, changes not staged for commit")
            elif working_sha1 == index_sha1 and index_sha1 != commit_sha1:
                print(f"{file} - file changed, changes staged for commit")
            elif index_sha1 != commit_sha1 and working_sha1 != index_sha1:
                print(f"{file} - file changed, different changes staged for commit")


