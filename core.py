#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  1 09:54:21 2022

@author: tyler
"""

import os
import hashlib
import json

class File:

    def __init__(self, filename, gethash=False):

        self.fullname = None
        self.location = None
        self.extension = None
        self.filesize = None
        self.hash = None
        self.last_modified = None
        self.last_accessed = None
        self.ctime = None

        if not os.path.isabs(filename):
            filename = os.path.asabs(filename)

        self.fullname = filename
        self.location, self.name = os.path.split(filename)

        try:
            self.extension = self.name.split('.')[-1]
        except IndexError:
            print(f'Could not identify file extension for file {filename}')
        try:
            self.filesize = os.path.getsize(self.fullname)
        except:
            print(f'Could not get file size for {self.fullname}')
        self.last_modified = os.path.getmtime(filename)
        self.last_accessed = os.path.getatime(filename)
        self.ctime = os.path.getctime(filename)

        if gethash: self.gethash()
        return

    def gethash(self, buffersize=2**20):
        hasher = hashlib.sha256()
        block = [None]
        with open(self.fullname, 'rb') as f:
            while len(block) > 0:
                block = f.read(buffersize)
                hasher.update(block)
        self.hash = hasher.hexdigest()
        return self.hash

    def asdict(self):
        decomposed = {
            'fullname':self.fullname,
            'size':self.filesize,
            'hash':self.hash,
            'modified':self.last_modified,
            'accessed':self.last_accessed,
            'created':self.ctime
            }
        return decomposed

    @staticmethod
    def fromdict(dictionary):
        fullname = dictionary['fullname']
        file = File(fullname)
        file.size = dictionary['size']
        file.hash = dictionary['hash']

        return file

    def delete(self):
        '''
        Deletes specified file from filesystem (if it exists)
        '''
        try:
            os.remove(self.fullname)
        except OSError:
            print(f'WARNING:File {self.fullname} could not be deleted!')
        return

class Directory:

    def __init__(self, location, gethash=False, filters=None):

        if not os.path.isabs(location):
            location = os.path.asabs(location)

        self.location = location
        self.contents = []
        for item in os.listdir(self.location):
            item = os.path.join(self.location, item)

            #Skip any items which match provided filters
            if filters is not None:
                hits = [f in item for f in filters]
                if any(hits):
                    continue

            if os.path.isdir(item):
                self.contents.append(Directory(item, gethash))
            else:
                self.contents.append(File(item, gethash))
        return

    def asdict(self):
        decomposed = {self.location:{}}
        toplevel = decomposed[self.location]
        for item in self:
            if type(item) is Directory:
                toplevel[item.location] = item.asdict()
            else:
                toplevel[item.fullname] = item.asdict()
        return decomposed

    def __iter__(self):
        for item in self.contents:
            yield item

    def save(self, filename):
        decomposed = self.asdict()
        decomposed = json.dumps(decomposed)
        with open(filename, 'w') as f:
            f.write(decomposed)
        return

    def find_duplicates(self, filters=None):
        flattened = self.flatten()
        hashes = {}

        for item in flattened:
            h = item.hash
            if h in hashes:
                hashes[h][0] += 1
                hashes[h].append(item)
            else:
                hashes[h] = [1,item]

        duplicates = {}
        for k, v in hashes.items():
            if v[0] > 1:
                duplicates[k] = v
        return duplicates

    def flatten(self):
        flattened = []
        for item in self:
            if type(item) is File:
                flattened.append(item)
            else:
                flattened += item.flatten()
        return flattened


def hash_file(fname, buffersize=2**20):
    hasher = hashlib.sha256()
    block = [None]
    with open(fname, 'rb') as f:
        while len(block) > 0:
            block = f.read(buffersize)
            hasher.update(block)
    hashed = hasher.hexdigest()
    return hashed

def build_filetree(root, buffersize=2**20, toplevel=True):
    tree = {}
    items = os.listdir(root)
    for item in items:
        abs_item = os.path.join(root, item)
        isdir = os.path.isdir(abs_item)
        if isdir:
            tree[abs_item] = build_filetree(abs_item, buffersize=buffersize)
        else:
            tree[abs_item] = hash_file(abs_item, buffersize=buffersize)
    return tree

def compare_directories(directory1, directory2):

    def flatten_directory(directory):
        flattened = []
        for item in directory:
            if type(item) is File:
                flattened.append(item.asdict())
            else:
                subdir = flatten_directory(item)
                flattened += subdir
        return flattened

if __name__ == '__main__':

    target_dir = r'/home/tyler/Documents/books/archive'

    filetree = Directory(target_dir, True)
    decomposed = filetree.asdict()
