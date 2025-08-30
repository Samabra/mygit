#!/usr/bin/env python3

import os
import sys
import re
import json
from helper import file_sha1sum, write_index

mygit = ".mygit"
branch_path = "refs/heads"
index_file = os.path.join(mygit, "index")
objects_dir = os.path.join(mygit, "objects")
branch_dir = os.path.join(mygit, branch_path)
head_file = os.path.join(mygit, "HEAD")
valid_file = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')


def get_from_blob(filename, sha1):
    blob_file = os.path.join(objects_dir, "blobs", sha1)
    with open(blob_file, "rb") as src, open(filename, "wb") as dst:
        dst.write(src.read())

def checkout_branch(branch):
    branch_file = os.path.join(branch_dir, branch)
    if not os.path.exists(branch_file):
        print(f"mygit-checkout: error: unknown branch '{branch}'", file=sys.stderr)
        sys.exit(1)
    with open(head_file, "r") as file:
        head_content = file.read().strip()
    current_branch = head_content.replace("ref: ", "")
    current_branch_file = os.path.join(mygit, current_branch)
    if os.path.samefile(branch_file, current_branch_file):
        print(f"Already on '{branch}'", file=sys.stderr)
        sys.exit(1)

    with open(branch_file, "r") as file:
        target_branch_commit_pointer = file.read().strip()
    
    with open(current_branch_file, "r") as file:
        current_branch_commit_pointer = file.read().strip()
    
    if current_branch_commit_pointer == target_branch_commit_pointer:
        with open(head_file, "w") as file:
            file.write(f"ref: refs/heads/{branch}\n")
        print(f"Switched to branch '{branch}'")
        sys.exit(0)
    
    def load_commit_file(commit_id):
        commit_file = os.path.join(objects_dir, f"{commit_id}.json")
        with open(commit_file, "r") as file:
            return json.load(file).get("files", {})
        
    with open(index_file, "r") as file:
        index_entries = [line.strip().split(None, 1) for line in file if line.strip()]
    index_map = {filename: sha1 for filename, sha1 in index_entries} if index_entries else {}

    target_commit = load_commit_file(target_branch_commit_pointer)
    current_commit = load_commit_file(current_branch_commit_pointer)

    diff_index_current_commit = sorted(
        file for file in (set(index_map) | set(current_commit))
        if index_map.get(file) != current_commit.get(file)
    )

    if diff_index_current_commit:
        print("mygit-checkout: error: Your changes to the following files would be overwritten by checkout:", file=sys.stderr)
        for file in diff_index_current_commit:
            print(file)
        sys.exit(1)
    
    working_files = sorted(
        file for file in os.listdir('.')
        if os.path.isfile(file) and valid_file.fullmatch(file)
    )
    
    working_map = {f: file_sha1sum(f) for f in working_files}

    overwrite = set()
    for file, sha1 in working_map.items():
        index_sha1 = index_map.get(file)
        target_sha1 = target_commit.get(file)

        if index_sha1 is None:
            if target_sha1 is not None:
                overwrite.add(file)
        else:
            if sha1 != index_sha1:
                if target_sha1 != sha1:
                    overwrite(file)
    if overwrite:
        print("mygit-checkout: error: Your changes to the following files would be overwritten by checkout:", file=sys.stderr)
        for file in sorted(set(overwrite)):
            print(file)
        sys.exit(1)
    
    previous_tracked = set(index_map.keys()) | set(current_commit.keys())
    target_set = set(target_commit.keys())

    
    with open(head_file, "w") as file:
        file.write(f"ref: refs/heads/{branch}\n")

    write_index(index_file, target_commit)

    for file in sorted(previous_tracked - target_set):
        if valid_file.fullmatch(file) and os.path.exists(file):
            os.remove(file)
    
    for file, sha1 in sorted(target_commit.items()):
        if valid_file.fullmatch(file):
            get_from_blob(file, sha1)
    print(f"Switched to branch '{branch}'")
    sys.exit(0)




flag_check = re.compile(r'^-[0-9]+$')
if not os.path.isdir(mygit):
    print("mygit-checkout: error: mygit repository directory .mygit not found", file=sys.stderr)
    sys.exit(1)

with open(".mygit/refs/heads/trunk", "r") as file:
    if not file.read().strip():
        print("mygit-checkout: error: this command can not be run until after the first commit", file=sys.stderr)
        sys.exit(1)

args = sys.argv[1:]

if not args or len(args) > 2 or (len(args) == 2 and "--" not in args):
    print("usage: mygit-checkout <branch>", file=sys.stderr)
    sys.exit(1)
elif len(args) == 1:
    branch = args[0]
    if branch.startswith("-"):
        if branch == "--" or not flag_check.fullmatch(branch):
            print("usage: mygit-checkout <branch>", file=sys.stderr)
            sys.exit(1)
    checkout_branch(branch)
else:
    if args[0] == "--":
        branch = args[1]
    elif args[1] == "--":
        if args[0].startswith("-") and not flag_check.fullmatch(args[0]):
            print("usage: mygit-checkout <branch>", file=sys.stderr)
            sys.exit(1)
        branch = args[0]
    checkout_branch(branch)



