# -*- coding: utf-8 -*-
"""
Created on Fri May  4 12:17:43 2018

@author: rober
"""

from node import Node
from node import NodeType, BRACKET_TYPES
import interpreter as intp
#from interpreter import Interpreter

CAPTURE = NodeType.CAPTURE

def key_from_name(name):
    return name, 0

def get_key(node):
    return node.val, node.id

def fill_in_form(form, mappings):
    form = form[:]
    
    for i in range(0, len(form)):
        node = form[i]
        if node.node_type is NodeType.CAPTURE:
            key = get_key(node)
            if key in mappings:
                form[i] = mappings[key]
        elif node.node_type in BRACKET_TYPES:
            new_nodes = fill_in_form(node.children, mappings)
            form[i] = Node(node.node_type, children=new_nodes)
        
    return form

def normal(val):
    return Node(NodeType.NORMAL, val=val)

def capture(val):
    return Node(NodeType.CAPTURE, val=val)

def bracket(b_type, children):
    return Node(b_type, children=children)

def paren(children):
    return bracket(NodeType.PAREN, children)

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

_paren = Bracket(NodeType.PAREN, '()')
_square = Bracket(NodeType.SQUARE, '[]')
_curly = Bracket(NodeType.CURLY, '{}')
BRACKETS = [_paren, _square, _curly]

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
    if token[0] == '~':
        return Node(NodeType.CAPTURE, val=token[1:])
    return Node(NodeType.NORMAL, val=token)

def get_name(macro):
    return macro.children[0]

def get_form(macro):
    return macro.children[1].children

def get_product(macro):
    return macro.children[2].children

def eval_macro(product, mappings, interpreter):
#    print('vvvvvvvv')
#    print('product: ' + str(product))
#    print('^^^^^^^^')
    if product[0].node_type != NodeType.FUNC:
        prod_result = fill_in_form(product, mappings)
        i = intp.Interpreter(interpreter.mcs_product) #No side effects if BALK
        evaluated = i.interpret_nodes(prod_result)[0] #The first should be either BALK or a PAREN
        if evaluated != normal('BALK'):
            evaluated = evaluated.children #Unwrap
            interpreter.set_mcs_product(i.mcs_product) #Now side effects take place
            return True, evaluated
        else:
            return False, None
    else: #product is a Python function mappings, interpreter -> nodes
        return product[0](mappings, interpreter)
    
not_match = False, {}
def matches(nodes, form, mappings=None, exact=False): #Return boolean and mappings
    mappings = mappings if mappings else {} #Initialize mappings
    
    m_len = len(form)
    
    if len(nodes) < m_len:
        return not_match
    if exact and len(nodes) > m_len:
        return not_match
    
    for i in range(0, m_len):
        n = nodes[i] #nodes is at least as long as form
        m = form[i]
        
        if m.node_type is CAPTURE:
            m_key = get_key(m)
            if m_key in mappings:
                captured = mappings[m_key]
                if n != captured:
                    return not_match
            else:
                mappings[m_key] = n
        elif m.node_type in BRACKET_TYPES:
            if n.node_type == m.node_type:
                bracket_match, mappings = matches(n.children, m.children, mappings=mappings, exact=True)
                if not bracket_match:
                    return not_match
            else:
                return not_match
        else:
            if n != m:
                return not_match
    
    return True, mappings