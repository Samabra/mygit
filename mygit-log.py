#!/usr/bin/env python3

import sys
import os
import re
import json
from datetime import datetime


mygit = ".mygit"
head_file = os.path.join(mygit, "HEAD")
objects_dir = os.path.join(mygit, "objects")

# Check if .mygit directory exists
if not os.path.isdir(mygit):
    print("mygit-log: error: mygit repository directory .mygit not found", file=sys.stderr)
    sys.exit(1)

# Regex to open commit files
commit_file_pattern = re.compile(r'[0-9]+.json')

# Get the current branch
with open(head_file, "r") as hf:
    head_content = hf.read().strip()
curr_branch_path = head_content.replace("ref: ", "")
curr_branch_file = os.path.join(mygit, curr_branch_path)

# Get the latest commit on current branch
with open(curr_branch_file, "r") as file:
    branch_tip = file.read().strip()

# Function for loading the commit file
def load_commit(commit_id: str):
    path = os.path.join(objects_dir, f"{commit_id}.json")
    with open(path, "r") as file:
        return json.load(file)

# Timestamp for extra tight security on ordering commits
# Global commit numbering does this as well but I put this here
# for fun
def parse(string):
    return datetime.fromisoformat(string)

# Travel through every commit like we are on a graph
# Basically find the parent/parents of a commit
# In a loop until we get to the first commit
seen = set()
stack = [branch_tip]
collected_commits = []

while stack:
    commit_id = stack.pop()
    if not commit_id or commit_id in seen:
        continue
    commit_file = load_commit((str(commit_id)))

    collected_commits.append(commit_file)
    seen.add(commit_id)

    parent1 = commit_file.get("parent")
    parent2 = commit_file.get("parent2")
    if parent1 is not None and parent1 != "":
        stack.append(str(parent1))
    if parent2 is not None and parent2 != "":
        stack.append(str(parent2))

# This is to order the commits in reverse, so the most previous one comes first
# It is also ordered on timestamp, which again I realise, at this point is for fun
collected_commits.sort(
    key=lambda c: (parse(c.get("timestamp", "")), int(c.get("commit_num", -1))),
    reverse=True
)

for commit in collected_commits:
    print(f"{commit.get('commit_num')} {commit.get('message', '')}")