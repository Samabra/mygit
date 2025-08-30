#!/usr/bin/env python3
import os
import sys

mygit = ".mygit"

# Initialise .mygit directory if .mygit directory doesn't exist
# Otherwise print a message saying that .mygit exists
if os.path.isdir(mygit):
    print("mygit-init: error: .mygit already exists", file=sys.stderr)
    sys.exit(1)

os.makedirs(mygit)

# Create index file where we will store all files
# added by .mygit-add. These files will be staged for 
# commit here
# The format of the index file is:
# Filename sha1sum_of_file
# This will track any changes to the name of a file as well
index_file = os.path.join(mygit, "index")
with open(index_file, "w") as f:
    pass

# Create a .mygit/objects directory for all the commits we create
# The commits are essentially going to be json files
objects = "objects"
objects_path = os.path.join(mygit, objects)
os.makedirs(objects_path, exist_ok=True)

# Create a .mygit/objects/blobs directory to store all the files we commit
# The files are named with the sha1sum of each file committed
blobs_dir = os.path.join(objects_path, "blobs")
os.makedirs(blobs_dir, exist_ok=True)

# Create a .mygit/refs/head directory with the branches. We will start with trunk
refs = "refs"
heads = "heads"
branch_dir = os.path.join(mygit, refs, heads)
os.makedirs(branch_dir, exist_ok=True)
initial_branch_file = os.path.join(branch_dir, "trunk")
with open(initial_branch_file, "w") as file:
    file.write("")

# Create a HEAD file to point to current branch
head_file = os.path.join(mygit, "HEAD")
with open(head_file, "w") as file:
    file.write("ref: refs/heads/trunk\n")

# Create a global sequence file, which will provide us our commit ID
seq_file = os.path.join(mygit, "SEQ")
with open(seq_file, "w") as file:
    file.write("-1\n")


# Print the confirmation message
print("Initialized empty mygit repository in .mygit")







