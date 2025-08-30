#!/usr/bin/env python3

import os
import sys
import re
import json
from datetime import datetime
from helper import file_sha1sum, read_seq, next_commit_id, bump_seq

mygit = ".mygit"
branch_path = "refs/heads"
index_file = os.path.join(mygit, "index")
objects_dir = os.path.join(mygit, "objects")
branch_dir = os.path.join(mygit, branch_path)
head_file = os.path.join(mygit, "HEAD")
blobs_dir = os.path.join(objects_dir, "blobs")
flag_check = re.compile(r'^-[0-9]+$')
commit_num_check = re.compile(r'[0-9]+')
valid_file = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')
seq_file = os.path.join(mygit, "SEQ")


def return_commit(commit_id: str):
    commit_file = os.path.join(objects_dir, f"{commit_id}.json")
    with open(commit_file, 'r') as commit:
        commit_data = json.load(commit)
    return commit_data.get("files", {})

def safe_return_commit(commit_id):
    if not commit_id:
        return {}
    return return_commit(commit_id)

def load_parent(commit_id):
    if commit_id is None or commit_id == "":
        return None
    commit_path = os.path.join(objects_dir, f"{commit_id}.json")
    with open(commit_path, "r") as file:
        parent = json.load(file).get("parent")
    return None if parent is None else str(parent)

def get_origin(current_commit_id, target_commit_id):
    if current_commit_id == target_commit_id:
        return current_commit_id
    ancestors = set()
    parent = current_commit_id
    while parent is not None:
        ancestors.add(parent)
        parent = load_parent(parent)

    parent_two = target_commit_id
    while parent_two is not None:
        if parent_two in ancestors:
            return parent_two
        parent_two = load_parent(parent_two)
    return None

if not os.path.isdir(mygit):
    print("mygit-merge: error: mygit repository directory .mygit not found", file=sys.stderr)
    sys.exit(1)

with open(".mygit/refs/heads/trunk", "r") as file:
    if not file.read().strip():
        print("mygit-merge: error: this command can not be run until after the first commit", file=sys.stderr)
        sys.exit(1)

args = sys.argv[1:]
if not args:
    print("usage: mygit-merge <branch|commit> -m message", file=sys.stderr)
    sys.exit(1)

if not "-m" in args and len(args) == 1:
    print("mygit-merge: error: empty commit message", file=sys.stderr)
    sys.exit(1)

if len(args) != 3:
    print("usage: mygit-merge <branch|commit> -m message", file=sys.stderr)
    sys.exit(1)

if not "-m" in args:
    print("usage: mygit-merge <branch|commit> -m message", file=sys.stderr)
    sys.exit(1)

if args[2] == "-m":
    print("usage: mygit-merge <branch|commit> -m message", file=sys.stderr)
    sys.exit(1)

if any(
    arg.startswith("-") and arg != "-m" and not flag_check.fullmatch(arg)
    for arg in args
):
    print("usage: mygit-merge <branch|commit> -m message", file=sys.stderr)
    sys.exit(1)

if args[0] == "-m":
    merge_target = args[2]
    message = args[1]
elif args[1] == "-m":
    merge_target = args[0]
    message = args[2]


with open(head_file, "r") as file:
    head_content = file.read().strip() 
current_branch_path = head_content.replace("ref: ", "")
current_branch = os.path.join(mygit, current_branch_path)

with open(current_branch, "r") as file:
    current_commit_id = file.read().strip()

target_commit_id = None
if commit_num_check.fullmatch(merge_target):
    commit_file = os.path.join(objects_dir, f"{merge_target}.json")
    if not os.path.exists(commit_file):
        print(f"mygit-merge: error: unknown commit '{merge_target}'", file=sys.stderr)
        sys.exit(1)
    target_commit_id = merge_target
else:
    branch_file = os.path.join(branch_dir, merge_target)
    if not os.path.exists(branch_file):
        print(f"mygit-merge: error: unknown branch '{merge_target}'", file=sys.stderr)
        sys.exit(1)
    with open(branch_file, "r") as file:
        target_commit_id = file.read().strip()

if target_commit_id == current_commit_id:
    print("Already up to date")
    sys.exit(0)

with open(index_file, "r") as file:
    index_entries = [line.strip().split(None, 1) for line in file if line.strip()]
index_map = {filename: sha1 for filename, sha1 in index_entries} if index_entries else {}

current_commit_files = safe_return_commit(current_commit_id)

diff_index_current_commit = sorted(
        file for file in (set(index_map) | set(current_commit_files))
        if index_map.get(file) != current_commit_files.get(file)
)

if diff_index_current_commit:
    print("mygit-merge: error: Your changes to the following files would be overwritten by merge:")
    for file in diff_index_current_commit:
        print(file)
    sys.exit(1)

working_files = sorted(
    file for file in os.listdir('.')
    if os.path.isfile(file) and valid_file.fullmatch(file)
)
def sha1(file): 
    return file_sha1sum(file) if os.path.exists(file) else None
tracked_dirty = sorted(
    file for file in index_map.keys()
    if (file in working_files and sha1(file) != index_map[file]) or (file not in working_files)
)

if tracked_dirty:
    print("mygit-merge: error: Your changes to the following files would be overwritten by merge:")
    for file in tracked_dirty:
        print(file)
    sys.exit(1)


target_commit_files = safe_return_commit(target_commit_id)
origin_commit_id = get_origin(current_commit_id, target_commit_id)

if origin_commit_id == current_commit_id:
    prev_set = set(current_commit_files.keys())
    target_set = set(target_commit_files.keys())

    for file in sorted(prev_set - target_set):
        if valid_file.fullmatch(file) and os.path.exists(file):
            os.remove(file)
    
    for file, sha1 in sorted(target_commit_files.items()):
        blob_path = os.path.join(blobs_dir, sha1)
        with open(blob_path, "rb") as src, open(file, "wb") as dst:
            dst.write(src.read())
    
    tmp = index_file + ".tmp"
    with open(tmp, "w") as file:
        for name, sha1 in sorted(target_commit_files.items()):
            file.write(f"{name} {sha1}\n")
    os.replace(tmp, index_file)

    with open(head_file, "r") as hf:
        head_content = hf.read().strip()
    curr_branch_path = head_content.replace("ref: ", "")
    curr_branch_file = os.path.join(mygit, curr_branch_path)
    with open(curr_branch_file, "w") as bf:
        bf.write(target_commit_id)

    print("Fast-forward: no commit created")
    sys.exit(0)


if origin_commit_id == target_commit_id:
    print("Already up to date")
    sys.exit(0)


origin_files = safe_return_commit(origin_commit_id)
C = current_commit_files
T = target_commit_files
O = origin_files
all_paths = sorted(set(C)| set(T)| set(O))

conflict = set()
merged = {}

# Decision function to decide which files on which branch to take
def decide(o, c, t):
    if c == t:
        return ("delete", None) if c is None else ("ok", c)
    if o is not None:
        if c == o and t != o:
            return ("ok", t)
        if c != o and t == o:
            return ("ok", c)
        if c is None and t == o:
            return ("delete", None)
        if t is None and c == o:
            return ("delete", None)
        return ("conflict", None)
    else:
        if c is None and t is None:
            return ("delete", None)
        if c is None and t is not None:
            return ("ok", t)
        if t is None and c is not None:
            return ("ok", c)
        return ("conflict", None)

for file in all_paths:
    c = C.get(file)
    t = T.get(file)
    o = O.get(file)

    status, branch = decide(o, c, t)
    if status == "ok" and branch is not None:
        merged[file] = branch
    elif status == "delete":
        pass
    elif status == "conflict":
        conflict.add(file)

if conflict:
    print("mygit-merge: error: These files can not be merged:")
    for file in conflict:
        print(file)
    sys.exit(1)


# Delete any files that are not in merge
delete_files = (set(C) | set(T)) - set(merged.keys())
for file in sorted(delete_files):
    if valid_file.fullmatch(file) and os.path.exists(file):
        os.remove(file)

for file, sha1 in sorted(merged.items()):
    blob_path = os.path.join(blobs_dir, sha1)
    with open(blob_path, "rb") as src, open(file, "wb") as dst:
        dst.write(src.read())

tmp = index_file + ".tmp"
with open(tmp, "w") as file:
    for name, sha1 in sorted(merged.items()):
        file.write(f"{name} {sha1}\n")
os.replace(tmp, index_file)

merge_commit_id = str(next_commit_id(seq_file))

# Write new commit file with two parents
timestamp = datetime.now().isoformat(timespec='seconds')
new_commit = {
    "commit_num": int(merge_commit_id),
    "parent": int(current_commit_id),
    "parent2": int(target_commit_id),
    "message": message,
    "timestamp": timestamp,
    "files": merged,
}
commit_path = os.path.join(mygit, "objects", f"{merge_commit_id}.json")
with open(commit_path, "w") as file:
    json.dump(new_commit, file, indent=4)

with open(current_branch, "w") as file:
    file.write(merge_commit_id)

bump_seq(seq_file, merge_commit_id)

print(f"Committed as commit {merge_commit_id}")
sys.exit(0)




    
    
    