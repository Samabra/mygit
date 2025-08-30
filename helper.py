#!/usr/bin/env python3
import hashlib
import os

# Get the sha1sum of a file
def file_sha1sum(filepath):
    h = hashlib.sha1()
    with open(filepath, 'rb') as file:
        while part := file.read(4096):
            h.update(part)
    return h.hexdigest()


# Read the current commit number we are on
def read_seq(seq_file):
    with open(seq_file, "r") as file:
        return int(file.read().strip())

# Return the next commit id
def next_commit_id(seq_file):
    last = read_seq(seq_file)
    return last + 1

# Increment commit number in SEQ file
def bump_seq(seq_file, new_last):
    tmp  = seq_file + ".tmp"
    with open(tmp, "w") as file:
        file.write(f"{new_last}")
    os.replace(tmp, seq_file)


def write_index(path, mapping: dict):
    tmp = path + ".tmp"
    with open(tmp, "w") as file:
        for name, sha1 in sorted(mapping.items()):
            file.write(f"{name} {sha1}\n")
    os.replace(tmp, path)