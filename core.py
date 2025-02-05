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

        self.long_name = None
        self.short_name = None
        self.location = None
        self.extension = None
        self.size = None
        self.hash = None
        self.last_modified = None
        self.last_accessed = None
        self.ctime = None
        self.tags = []

        if not os.path.isabs(filename):
            filename = os.path.asabs(filename)

        self.long_name = filename
        self.location, self.short_name = os.path.split(filename)

        try:
            self.extension = self.short_name.split('.')[-1]
        except IndexError:
            print(f'Could not identify file extension for file {filename}')
        try:
            self.size = os.path.getsize(self.long_name)
        except:
            print(f'Could not get file size for {self.long_name}')
        self.last_modified = os.path.getmtime(self.long_name)
        self.last_accessed = os.path.getatime(self.long_name)
        self.ctime = os.path.getctime(self.long_name)

        if gethash: self.gethash()
        return
    
    def add_tag(self, tag):
        if tag in self.tags:
            print(f'File {self.long_name} already tagged "{tag}".')
        else:
            self.tags.append(tag)
        return
    
    def remove_tag(self, tag):
        if tag not in self.tags:
            print(f'Tag "{tag}" not found for file {self.long_name}.')
        else:
            self.tags.remove(tag)
        return

    def gethash(self, buffersize=2**20):
        '''
        Calculate SHA-256 hash of file.

        Parameters
        ----------
        buffersize : int, optional
            Size of buffer for digesting file, in bytes. The default is 2**20.

        Returns
        -------
        self.hash : str
            SHA-256 hash of file.
        '''
        hasher = hashlib.sha256()
        
        block = [None]
        with open(self.long_name, 'rb') as f:
            while len(block) > 0:
                block = f.read(buffersize)
                hasher.update(block)
        self.hash = hasher.hexdigest()
        return self.hash

    def decompose(self):
        '''
        Decomposes File object to dictionary.

        Returns
        -------
        decomposed : dict
            Dictionary containing file metadata.
        '''
        
        decomposed = {
            'fullname':self.long_name,
            'size':self.size,
            'hash':self.hash,
            'modified':self.last_modified,
            'accessed':self.last_accessed,
            'created':self.ctime,
            'tags':self.tags
            }
        return decomposed

    @staticmethod
    def fromdict(dictionary):
        '''
        Generates File object from metadata dictionary.

        Parameters
        ----------
        dictionary : dict
            Dictionary containing file metadata.

        Returns
        -------
        file : File
            Reconstituted File object.

        '''
        fullname = dictionary['fullname']
        file = File(fullname)
        file.size = dictionary['size']
        file.hash = dictionary['hash']
        file.last_mofified = dictionary['modified']
        file.last_accessed = dictionary['accessed']
        file.ctime = dictionary['created']
        file.tags = dictionary['tags']

        return file

    def delete(self):
        '''
        Deletes the file from filesystem (if it exists).
        '''
        try:
            os.remove(self.long_name)
        except OSError:
            print(f'WARNING:File {self.fullname} could not be deleted!')
        return
    
class FileTree(dict):
    
    def __init__(self):
        dict.__init__(self)
        self.root = None
        self.size = 0.0
        return
    
    def __iter__(self):
        for item in self.items():
            yield item
    
    def decompose(self):
        toplevel = {}
        
        for name, item in self:
            if type(item) is FileTree:
                subdir_decomposed = item.decompose()[item.root]
                toplevel[item.root] = subdir_decomposed
            else:
                toplevel[item.long_name] = ['file', item.decompose()]
                
        decomposed = {self.root: ['dir', toplevel]}
        return decomposed
    
    def save(self, filename):
        decomposed = self.decompose()
        decomposed = json.dumps(decomposed)
        with open(filename, 'w') as f:
            f.write(decomposed)
        return
    
    @staticmethod
    def from_dict(decomposed):
        
        filetree = FileTree()
        filetree.root = list(decomposed.keys())[0]
        for key, (item_type, item) in decomposed.items():
            if item_type == 'file':
                file = File.fromdict(item)
                filetree[file.short_name] = File
                filetree.size += file.size
            elif item_type == 'dir':
                subdir = FileTree.from_dict(item)
                filetree[os.path.split(key)[1]] = subdir
                filetree.size += subdir.size
                
        return filetree
    
    @staticmethod
    def from_path(path, gethash=False, filters=[]):
        if not os.path.isabs(path):
            path = os.path.asabs(path)
        filetree = FileTree()
        filetree.root = path
        for item in os.listdir(path):

            #Skip any items which match provided filters
            if item in filters:
                continue
            
            fullpath = os.path.join(path, item)

            if os.path.isdir(fullpath):
                subdir = FileTree().from_path(fullpath, filters)
                filetree[item] = subdir
                filetree.size += subdir.size
            else:
                file = File(fullpath, gethash)
                filetree[item] = file
                filetree.size += file.size
                
        return filetree
        
    
    @staticmethod
    def from_json(jsond):
        decomposed = json.loads(jsond)
        filetree = FileTree().from_dict(decomposed)        
        return filetree
    
    @staticmethod
    def load(filename):
        with open(filename, 'r') as f:
            jsond = f.read()
        filetree = FileTree.from_json(jsond)
        return filetree[list(filetree.keys())[0]]

    def find_duplicates(self, filters=None):
        flattened = self.flatten()
        hashes = {}

        for path, item in flattened.items():
            h = item.hash
            if h is None:
                item.gethash()
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
        flattened = {}
        for path, item in self:
            if type(item) is File:
                flattened[item.long_name] = item
            else:
                subdir_flat = item.flatten()
                for path, item in subdir_flat.items():
                    flattened[path] = item
        return flattened

class Directory(dict):

    def __init__(self, root, gethash=False, filters=[]):
        
        dict.__init__(self)
        self.long_name = None           #Absolute directory path
        self.short_name = None          #Relative directory path
        self.size = 0.0                 #Cumulative size of objects in directory and all subdirectories, in bytes
        self.tags = []
        self.filetree = None
        
        if not os.path.isabs(root):
            root = os.path.asabs(root)
        self.long_name = root
        self.short_name = os.path.split(self.long_name)[-1]
        
        self.populate_filetree(gethash, filters)
        
        self.size = float(self.filetree.size)
        
        return

    def __iter__(self):
        for item in self.filetree.items():
            yield item
            
    def find_duplicates(self):
        return self.filetree.find_duplicates()
    
    def populate_filetree(self, gethash=False, filters=[]):
        self.filetree = FileTree().from_path(self.long_name)                
        return
    
                
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
    tree = Directory(root)
    for item in tree.contents:
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
                flattened.append(item.decompose())
            else:
                subdir = flatten_directory(item)
                flattened += subdir
        return flattened


if __name__ == '__main__':

    target_dir = r'/home/tyler/Documents/books/archive'

    filetree = Directory(target_dir, True)
    decomposed = filetree.decompose()
