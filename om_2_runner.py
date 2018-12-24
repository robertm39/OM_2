# -*- coding: utf-8 -*-
"""
Created on Sun Apr 29 13:53:45 2018

@author: rober
"""

import os

ext = '.om2'

def add_om2_extension(file):
    """
    Return the file with the .om2 extension on the end.
    
    Parameters:
        file: The file to return with the .om2 extension.
    """
    #Assume that any file without a .om extension has no extension at all
    if not file[:-3] == ext:
        return file + ext 
    return file

def run_file(file, interpreter):
    """
    Run a file without importing.
    
    Parameters:
        file: The om2 file to run.
        interpreter: The interpreter to run the file in.
    """
    text = ''
    with open(file) as f:
        for line in f:
            line = line.strip()
            if len(line) > 0 and not line[0] in ['#', '@']: #Remove imports and comments
                text += line + ' '
    return interpreter.interpret(text)

def get_files_from_folder(folder):
    """
    Return the main path, a dict from names of files in the folder to paths, and a list of files in the folder.
    
    Parameters:
        folder: The folder to return main, paths_from_names, and files from.
    """
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
    return main, paths_from_names, files

def get_imports(files, paths_from_names):
    """
    Return a dict from files to a list of files they import.
    
    Parameters:
        files: The files to get imports from'
        paths_from_names: A dict from files to filepaths.
    """
    imports = {} #A dict from files to files they import
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
    
    return imports

def get_needed(files, imports):
    """
    Return a map from files to a list of files that the file needs run before.
    
    Parameters:
        files: The list of files to return a dict for.
        imports: A dict from files to files they import.
    """
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
    
    return needed

def check_for_circularity(to_check, needed):
    """
    Throw an assertion error if a file needs itself.
    
    Parameters:
        to_check: The files to check for circularities.
        needed: A dict from files to a list of all files they need.
    """
    for file in to_check:
        if file in needed[file]:
            raise AssertionError('Circular dependency at ' + file)

def run_needed_files(to_run, needed, interpreter):
    """
    Run all files in to run, only running a file if all files it needs have been run.
    
    Parameters:
        to_run: The files to run.
        needed: A dict from files to a list of all files they need.
        interpreter: The interpreter to run the files in.
    """
    run = []
    while to_run:
        for file in to_run:
            #Only run this file if all the files it needs have already been run
            if not [file for file in needed[file] if not file in run]:
                run_file(file, interpreter)
                run.append(file)
                to_run.remove(file)

def run_om2_project(folder, interpreter):
    """
    Run an om2 project.
    
    Parameters:
        folder: The folder containing the project.
        interpreter: The interpreter to run the project in.
    """
    
    main, paths_from_names, files = get_files_from_folder(folder)
    imports = get_imports(files, paths_from_names)
    needed = get_needed(files, imports)
    
    to_check = [main] + needed[main]
    check_for_circularity(to_check, needed)
    
    run_needed_files(needed[main], needed, interpreter)
                
    return run_file(main, interpreter)