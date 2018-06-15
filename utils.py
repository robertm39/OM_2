# -*- coding: utf-8 -*-
"""
Created on Fri May  4 12:17:43 2018

@author: rober
"""

import om
from node import Node
from node import NodeType
from node import DEF_NODE

def key_from_name(name):
    return name, 0

def get_key(node):
    return node.val, node.id

def fill_in_form(form, mappings):
    form = form[:]
    
    i = 0
    for node in form:
        if node.node_type is NodeType.CAPTURE:
            key = get_key(node)
            if key in mappings:
                form[i] = mappings[key]
        elif node.node_type in om.BRACKET_TYPES:
            new_nodes = fill_in_form(node.children, mappings)
            form[i] = Node(node.node_type, children=new_nodes)
        i += 1
        
    return form

def normal(val):
    return Node(NodeType.NORMAL, val=val)

def capture(val):
    return Node(NodeType.CAPTURE, val=val)

def unpack_and_wrap_node(node):
    if node.node_type is NodeType.PAREN:
        return node.children
    return [node]


BRACKET_DICT = {}
ESCAPE = '`'
WHITESPACE = [' ', '\n', '\t', '\r']

class Bracket:
    def __init__(self, node_type, text):
        self.node_type = node_type
        self.left = text[0]
        self.right = text[1]
        
        BRACKET_DICT[self.left] = self
        BRACKET_DICT[self.right] = self
        
    def __getitem__(self, index):
        return self.left if index == 0 else self.right if index == 1 else None

BRACKET_TYPES = [NodeType.PAREN, NodeType.SQUARE, NodeType.CURLY]

paren = Bracket(NodeType.PAREN, '()')
square = Bracket(NodeType.SQUARE, '[]')
curly = Bracket(NodeType.CURLY, '{}')
BRACKETS = [paren, square, curly]

def matching_bracket_index(line, ind):
    s_ind = ind
    bracket = line[ind]
    if not bracket in BRACKET_DICT:
        print(bracket)
        raise AssertionError

    bracket_type = BRACKET_DICT[bracket]
    direction = 1 if bracket == bracket_type[0] else -1

    num = 1
    while num != 0 and 0 <= ind < len(line):
        ind = ind + direction
        try:
            char = line[ind]
        except IndexError:
            print('Unmatched bracket:')
            print(' ' * s_ind + 'v')
            print(line)
            raise ValueError
        if ind == 0 or not line[ind-1] in ESCAPE:
            if char == bracket_type[0]:
                num += direction
            elif char == bracket_type[1]:
                num -= direction
    if num != 0:
        raise AssertionError
    return ind

def tokenize(line):
    tokens = []

    curr_token = ''
    escaping = 0
    
    ind = 0
    for char in line + ' ':
        if escaping > 0:
            curr_token += char
            escaping -= 1
        elif char in BRACKET_DICT:
            tokens.append(curr_token)
            curr_token = ''
            
            curr_token += char
            next_bracket = matching_bracket_index(line, ind)
            if next_bracket > ind: #We're at the beginning of a bracket
                escaping = next_bracket - ind #skip to the next bracket
            else: #We're at the end of a bracket
                tokens.append(curr_token) #The current token is finished
                curr_token = ''
        elif char in WHITESPACE:
            tokens.append(curr_token) #We're not escaping, so we're not in brackets
            curr_token = ''
        elif char in ESCAPE:
            escaping += 1
        else:
            curr_token += char
        ind += 1 #Update index for next letter
            
    return [t for t in tokens if t] #Get rid of empty tokens

def parse(token):
    for bracket in BRACKETS:
        if token[0] == bracket[0] and token[-1] == bracket[1]:
            text = token[1:-1]
            child_tokens = tokenize(text)
            children = [parse(token) for token in child_tokens]
            
            node = Node(bracket.node_type, children=children)
            return node
#    if token[0] == '~':
#        text = token[1:]
#        node = Node(NodeType.CAPTURE, val=text)
#        return node
    if token == DEF_NODE.val:
        return DEF_NODE
    return Node(NodeType.NORMAL, val=token)