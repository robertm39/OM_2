# -*- coding: utf-8 -*-
"""
Created on Sun Apr 29 17:09:08 2018

@author: rober
"""

import om_2_runner

#shell = om.Shell()
folder = 'C:\\Users\\rober\\.spyder-py3\\Robert_Python\\om_2\\om_2_Test_Project'
#om_runner.run_om_project(folder, shell)

def add_base_code(interpreter):
    om_2_runner.run_om2_project(folder, interpreter)