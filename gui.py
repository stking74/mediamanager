import tkinter as tk
from tkinter import ttk
from .core import File, Directory
import time
import os

class Window:

    def __init__(self, master):
        if  master == self:
            self.root = master.root
            self.master = None
        else:
            self.master = master
            self.root = tk.Toplevel()
        self.frame = tk.Frame(self.root)
        self.frame.grid()
        return
    
    def close(self):
        self.frame.destroy()
        return

class Master(Window):

    def __init__(self):

        self.root = tk.Tk()
        Window.__init__(self, self)
        self.populate()
        self.root.mainloop()

    def populate(self):
        
        #Labels and readouts
        tk.Label(self.frame, text='Settings:').grid(column=0, row=0)
        self.statusReadout = tk.Label(self.frame, text='Ready')
        self.statusReadout.grid(column=0, row=2)
        
        #Buttons        
        tk.Button(self.frame, text='Scan', command=self.run_scan).grid(column=0, row=1)
        
        #Entries and settings
        tk.Label(self.frame, text='Target Directory:').grid(column=1, row=0)
        self.targetdir_entry = tk.Entry(self.frame)
        self.targetdir_entry.grid(column=2, row=0)
        tk.Label(self.frame, text='Hash:').grid(column=1, row=1)
        self.hashBool = tk.BooleanVar()
        tk.Checkbutton(self.frame, variable=self.hashBool, ).grid(column=2, row=1)
        
        return

    def run_scan(self):
        self.statusReadout.config(text='Scanning directory...')
        
        #Check settings
        hashcheck = self.hashBool.get()
        target = self.targetdir_entry.get()
        target = r'{}'.format(target)
        
        assert os.path.isdir(target)
        
        #perform scan
        directory = Directory(target, gethash=hashcheck)
        
        #post results
        self.statusReadout.config(text='Scan finished')
        self.post_result(directory)
        
    def post_result(self, directory):
        self.result_gui = ScanResult(directory, master=self)
        return
    
    def close_result(self):
        self.result_gui.close()
        self.result_gui = None
        return

class Slave(Window):

    def __init__(self, master):
        
        self.master = master
        Window.__init__(self, self.master)
        return

class ScanResult(Slave):

    def __init__(self, directory, master):
        self.directory = directory
        Slave.__init__(self, master)
        self.populate()
        self.root.mainloop()
        return
    
    def close_nicely(self):
        self.frame.destroy()
        return
    
    def duplicate_search(self):
        flattened = self.directory.flatten()
        unique_hashes = set()
        all_hashes = []
        for file in flattened:
            if file.hash is None: file.gethash()
            unique_hashes.add(file.hash)
            all_hashes.append(file.hash)
            
        matches = {}
        for h in list(unique_hashes):
            if all_hashes.count(h) > 2:
                hits = []
                for file in flattened:
                    if file.hash == h:
                        hits.append(file.fullname)
                matches[h] = hits
        return matches

    def populate(self):
        
        #Extract report info
        flat = self.directory.flatten()
        n_files = len(flat)
        total_size = 0
        for f in flat:
            total_size += f.filesize
        #Basic info
        
        #Labels
        tk.Label(self.frame, text='Absolute path:').grid(column=0, row=0)
        tk.Label(self.frame, text='Total Files:').grid(column=0,row=1)
        tk.Label(self.frame, text='Total directory size:').grid(column=0,row=2)
        #Data
        tk.Label(self.frame, text=self.directory.location).grid(column=1, row=0)
        tk.Label(self.frame, text=n_files).grid(column=1, row=1)
        tk.Label(self.frame, text=f'{total_size/(1000**2)} MB').grid(column=1, row=2)
        #Buttons
        tk.Button(self.frame, text='Close', command=self.close_nicely).grid(column=2, row=5)
        tk.Button(self.frame, text='Find Duplicates', command=self.duplicate_search).grid(column=1, row=5)
        
        self.table = ttk.Treeview(self.frame)
        self.table['columns'] = ('index','folder','filename','size','hash','extension')
        self.table.column('#0', width=0, stretch=False)
        self.table.column('index', anchor='n', width=5)
        self.table.column('folder', anchor='n', width=5)
        self.table.column('filename', anchor='n')
        self.table.column('size', anchor='n')
        self.table.column('hash', anchor='n')
        self.table.column('extension', anchor='n')
        # table.column('modified', anchor='n', width=50)
        self.table.heading('#0', text='', anchor='n')
        self.table.heading('index', text='Index', anchor='n')
        self.table.heading('folder', text='Folder', anchor='n')
        self.table.heading('filename', text='Filename', anchor='n')
        self.table.heading('size', text='Size (MB)', anchor='n')
        self.table.heading('hash', text='Hash', anchor='n')
        self.table.heading('extension', text='Extension', anchor='n')
        # table.heading('modified', text='Modified', anchor='n')
        
        # sb = tk.Scrollbar(self.frame, orient='vertical')
        # sb.config(command=sb.yview)
        for i, item in enumerate(flat):
            index = i + 1
            filename = item.fullname
            folder, fname = os.path.split(filename)
            size = item.filesize / (1000**2)
            size = f'{size:.05}'
            filehash = item.hash
            extension = filename.split('.')[-1].lower()
            packaged = (index, folder, fname, size, filehash, extension)
            self.table.insert(parent='', index=index, iid=i, text='', values=packaged)
        self.table.grid(column=2, row=4)
        # listbox.grid(column=0, row=3)
        # sb.grid(column=2,row=3)
        # tk.Button(self.frame, text='Close', command=self.master.result_gui.close)
        return
    
    
