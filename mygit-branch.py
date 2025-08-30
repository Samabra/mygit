#!/usr/bin/env python3

import os
import sys
import re
import json

mygit = ".mygit"
branch_path = "refs/heads"
branch_dir = os.path.join(mygit, branch_path)
head_file = os.path.join(mygit, "HEAD")
objects_dir = os.path.join(mygit, "objects")

def get_current_commit():
    with open(head_file, "r") as file:
        head_content = file.read().strip()
    branch_path = head_content.replace("ref: ", "")
    branch_file = os.path.join(mygit, branch_path)

    with open(branch_file, "r") as file:
        return file.read().strip()
    
def read_branch_commit(branch_file_path):
    with open(branch_file_path, "r") as file:
        return file.read().strip()
def load_parents(commit_id: str):
    path = os.path.join(objects_dir, f"{commit_id}.json")
    with open(path, "r") as file:
        commit_data = json.load(file)
    parents = []
    parent1 = commit_data.get("parent")
    parent2 = commit_data.get("parent2")
    if parent1 is not None:
        parents.append(parent1)
    if parent2 is not None:
        parents.append(parent2)
    return parents

 # Get the ancestor commit of the current commit in branch
def is_ancestor(ancestor, current):
    if ancestor == current:
        return True
    seen = set()
    stack = [current]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        for parent in load_parents(node):
            if parent == ancestor:
                return True
            stack.append(parent)
    return False
if not os.path.isdir(mygit):
    print("mygit-branch: error: mygit repository directory .mygit not found", file=sys.stderr)
    sys.exit(1)


delete_flag = re.compile(r'^-[d]+$')
options_end_flag = "--"
flag_check = re.compile(r'^-[0-9]+$')
valid_branch = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$')

delete = False

with open(".mygit/refs/heads/trunk", "r") as file:
    if not file.read().strip():
        print("mygit-branch: error: this command can not be run until after the first commit", file=sys.stderr)
        sys.exit(1)

if len(sys.argv) == 1:
    branches = []

    # Print all branches in sorted order
    for file in os.listdir(branch_dir):
        if file != "trunk":
            branches.append(file)
    
    for branch in sorted(branches):
        print(branch)
    print("trunk")

elif len(sys.argv) == 2:
    command = sys.argv[1]
    delete = True if delete_flag.fullmatch(command) else False

    if delete:
        print("mygit-branch: error: branch name required", file=sys.stderr)
        sys.exit(1)
    elif command.startswith('-') and command != options_end_flag:
        if flag_check.fullmatch(command) or command == "-":
            print(f"mygit-branch: error: invalid branch name '{command}'", file=sys.stderr)
            sys.exit(1)
        else:
            print("usage: mygit-branch [-d] <branch>", file=sys.stderr)
            sys.exit(1)
    elif not valid_branch.fullmatch(command):
        print(f"mygit-branch: error: invalid branch name '{command}'", file=sys.stderr)
        sys.exit(1)
    else:
        if command == options_end_flag:
            branches = []
            for file in os.listdir(branch_dir):
                if file != "trunk":
                    branches.append(file)
            
            for branch in sorted(branches):
                print(branch)
            print("trunk")
            sys.exit(0)
        else:   
            new_branch = command
            new_branch_file = os.path.join(branch_dir, new_branch)
            if os.path.exists(new_branch_file):
                print(f"mygit-branch: error: branch '{new_branch}' already exists", file=sys.stderr)
                sys.exit(1)
            current_commit = get_current_commit()
            with open(new_branch_file, "w") as file:
                file.write(current_commit)
            sys.exit(0)

elif len(sys.argv) == 3:
    args = sys.argv[1:]
    delete = any(delete_flag.fullmatch(arg) for arg in args)
    if options_end_flag in args:
        if args[0] == options_end_flag:
            if not valid_branch.fullmatch(args[1]):
                print(f"mygit-branch: error: invalid branch name '{args[1]}'", file=sys.stderr)
                sys.exit(1)
            else:
                new_branch = args[1]
                new_branch_file = os.path.join(branch_dir, new_branch)
                if os.path.exists(new_branch_file):
                    print(f"mygit-branch: error: branch '{new_branch}' already exists", file=sys.stderr)
                    sys.exit(1)
                with open(new_branch_file, "w") as file:
                    pass
                sys.exit(0)
        else:
            if flag_check.fullmatch(args[0]):
                print(f"mygit-branch: error: invalid branch name '{args[0]}'", file=sys.stderr)
                sys.exit(1)
            elif args[0].startswith("-"):
                print("usage: mygit-branch [-d] <branch>")
                sys.exit(1)
            elif not valid_branch.fullmatch(args[0]):
                print(f"mygit-branch: error: invalid branch name '{args[0]}'", file=sys.stderr)
                sys.exit(1)
            else:
                new_branch = args[0]
                new_branch_file = os.path.join(branch_dir, new_branch)
                if os.path.exists(new_branch_file):
                    print(f"mygit-branch: error: branch '{new_branch}' already exists", file=sys.stderr)
                    sys.exit(1)
                current_commit = current_commit()
                with open(new_branch_file, "w") as file:
                    file.write(current_commit)
                sys.exit(0)
    elif not delete:
        print("usage: mygit-branch [-d] <branch>", file=sys.stderr)
        sys.exit(1)
    elif delete:
        if args[0] == options_end_flag:
            print(f"mygit-branch: error: invalid branch name '{args[1]}'", file=sys.stderr)
            sys.exit(1)
        elif delete_flag.fullmatch(args[1]) or args[1] == options_end_flag:
            print(f"mygit-branch: error: branch name required", file=sys.stderr)
            sys.exit(1)
        elif any(arg.startswith("-") and not (delete_flag.fullmatch(arg) or arg == "--") for arg in args):
            index = next(
                (i for i, arg in enumerate(args)
                if arg.startswith("-") and not (delete_flag.fullmatch(arg) or arg == "--")),
                None
            )
            if flag_check.fullmatch(args[index]):
                print(f"mygit-branch: error: invalid branch name '{args[index]}'", file=sys.stderr)
                sys.exit(1)
            else:
                print("hello")
                print("usage: mygit-branch [-d] <branch>", file=sys.stderr)
                sys.exit(1)
        elif any(not valid_branch.fullmatch(arg) and not (delete_flag.fullmatch(arg) or arg =="--") for arg in args):
            index = next(
                (i for i, arg in enumerate(args)
                if not valid_branch.fullmatch(arg) and not (delete_flag.fullmatch(arg) or arg == "--")),
                None
            )
            print(f"mygit-branch: error: invalid branch name '{args[index]}'", file=sys.stderr)
            sys.exit(1)
        else:
            index = next(
                (i for i, arg in enumerate(args)
                if valid_branch.fullmatch(arg) and not delete_flag.fullmatch(arg))
            )
            branch_delete = args[index]
            branch_delete_file = os.path.join(branch_dir, branch_delete)
            if not os.path.exists(branch_delete_file):
                print(f"mygit-branch: error: branch '{branch_delete}' doesn't exist", file=sys.stderr)
                sys.exit(1)
            if branch_delete == "trunk":
                print(f"mygit-branch: error: can not delete branch '{branch_delete}': default branch ", file=sys.stderr)
                sys.exit(1)
            
            with open(head_file, "r") as file:
                current_branch = file.read().strip()
            current_branch_path = current_branch.replace("ref: ", "")
            current_branch_file = os.path.join(mygit, current_branch_path)

            if os.path.samefile(current_branch_file, branch_delete_file):
                print(f"mygit-branch: error: can not delete '{branch_delete}': current branch", file=sys.stderr)
                sys.exit(1)
            current_tip = get_current_commit()
            with open(branch_delete_file, "r") as file:
                delete_commit = file.read().strip()
            
            if not is_ancestor(delete_commit, current_tip):
                print(f"mygit-branch: error: branch '{branch_delete}' has unmerged changes", file=sys.stderr)
                sys.exit(1)
            
            os.remove(branch_delete_file)
            print(f"Deleted branch '{branch_delete}'")
            sys.exit(0)
else:
    print("usage: mygit-branch [-d] <branch>")
    sys.exit(1)
    
