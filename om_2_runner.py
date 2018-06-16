# -*- coding: utf-8 -*-
"""
Created on Sun Apr 29 13:53:45 2018

@author: rober
"""

import os

ext = '.om2'

def add_om2_extension(file):
    #Assume that any file without a .om extension has no extension at all
    if not file[:-3] == ext:
        return file + ext 
    return file

def run_file(file, shell):
    text = ''
    with open(file) as f:
        for line in f:
            line = line.strip()
            if len(line) > 0 and not line[0] in ['#', '@']: #Remove imports and comments
                text += line + ' '
    return shell.interpret(text, return_nodes=True)

def run_om2_project(folder, shell):
    files = []
    #Walk through the folder, collecting all files
    main = ''
    
    paths_from_names = {}
    for (dirpath, dirnames, filenames) in os.walk(folder):
        for file in filenames:
            paths_from_names[file] = os.path.join(dirpath, file)
        paths = [paths_from_names[f] for f in filenames]
        if 'main' + ext in filenames:
            main = os.path.join(dirpath, 'main' + ext)
        files.extend(paths)
    
    #Only keep .om files
    files = [file for file in files if os.path.splitext(file)[1] == ext]
    
    imports = {} #A map from files to files they import
    #Find what files each file needs
            
    for file in files:
        with open(file) as f:
            
            for line in f:
                to_add = []
                line = line.strip()
                if len(line) > 0 and line[0] == '@':
                    line = line [1:]
                    names = line.split()
                    names = [add_om2_extension(name) for name in names]
                    names = [paths_from_names[name] for name in names]
                    to_add.extend(names)
                imports[file] = imports.get(file, []) + to_add
    #Find which files main.om needs directly or indirectly
    needed = {} #A map a file to all the files that file needs, directly or indirectly
    for file in imports:
        needed[file] = imports[file]
    #Repeatedly, for each file, add the needed files of the files it imports to its needed files
    going = True
    while going:
        going = False
        for file in files:
            add = []
            for imported in imports[file]:
                add.extend(needed.get(imported, []))
            prev = needed.get(file, [])
            new = prev[:]
            new.extend(add)
            new = list(set(new))
            if set(prev) != set(new):
                going = True
            
            needed[file] = new
    
    #Check for circularity
    to_check = [main] + needed[main]
    for file in to_check:
        if file in needed[file]:
            raise AssertionError('Circular dependency at ' + file)
    
    to_run = needed[main]
    run = []
    while to_run:
        for file in to_run:
            if not [file for file in needed[file] if not file in run]:
                run_file(file, shell)
                run.append(file)
                to_run.remove(file)
                
    return run_file(main, shell)