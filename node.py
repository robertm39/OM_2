# -*- coding: utf-8 -*-
"""
Created on Fri May  4 15:32:40 2018

@author: rober
"""

from enum import Enum

class NodeType(Enum):
    PAREN = 'PAREN'     #()
    SQUARE = 'SQUARE'   #[]
    CURLY = 'CURLY'     #{}
    CAPTURE = 'CAPTURE' #cap word (The cap macro)
    NORMAL = 'NORMAL'   #word
    FUNC = 'FUNC' #A python function; for python function macros

BRACKET_TYPES = [NodeType.PAREN, NodeType.SQUARE, NodeType.CURLY]

class Node:
    def __init__(self, node_type, val='', children=[], func=None):
        self.node_type = node_type
        self.val = val
        self.v_hash = hash(self.val)
        self.children = children[:]
        self.func = func
        self.id = 0 #The common id
    
    def copy(self):
        c_copy = [c.copy() for c in self.children]
        return Node(self.node_type, self.val, c_copy)
    
    def __call__(self, mappings, interpreter):
        return self.func(mappings, interpreter)
    
    def __str__(self, depth=0):
        id_part = '::' + str(self.id) if self.id != 0 else ''
        result = '(' + str(self.node_type)[9:] + '::' + str(self.val) + id_part + ')'
#        result = result[0] + result[1:-1].strip() + result[-1] #Get rid of internal edge whitespace
        result = '\t' * depth + result + '\n'
        for child in self.children:
            result += child.__str__(depth=depth+1)
        
        return result
    
    def __repr__(self):
        return str(self)
    
    def __eq__(self, other):
        if other == None:
            return False
        if self.val != other.val:
            return False
        if self.children != other.children:
            return False
        if self.node_type != other.node_type:
            return False
        if self.id != other.id:
            return False
        return True
    
    def __ne__(self, other):
        return not (self == other)
    
    def __hash__(self):
        result = 17
        result += self.v_hash
        result *= 31
        result += self.id
        result *= 31
        return result