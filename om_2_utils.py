# -*- coding: utf-8 -*-
"""
Created on Fri May  4 12:17:43 2018

@author: rober
"""

from node import Node, NodeType, BRACKET_TYPES
import interpreter as intp
#from interpreter import Interpreter

CAPTURE = NodeType.CAPTURE

def key_from_name(name):
    """
    Return a dict key that uniquely identifies a node with the given name and zero id.
    
    Parameter:
        name: The name to return a key for.
    """
    return name, 0

def get_key(node):
    """
    Return a dict key that uniquely identifies the node.
    
    Parameters:
        node: The node to return a key for.
    """
    return node.val, node.id

def fill_in_form(form, mappings):
    """
    Return the form with capture nodes replaced with the apppropriate mappings.
    
    Parameters:
        form: The form to fill in.
        mappings: The mappings from capture nodes to expressions.
    """
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
    """
    Return a normal node with val as its value.
    
    Parameters:
        val: The value for the normal node to have.
    """
    return Node(NodeType.NORMAL, val=val)

def capture(val):
    """
    Return a capture node with val as its value.
    
    Parameters:
        val: The value for the capture node to have.
    """
    return Node(NodeType.CAPTURE, val=val)

def bracket(b_type, children):
    """
    Return a bracket node with b_type as its type and children as its children.
    
    Parameters:
        b_type: The type for the node to have.
        children: The children for the node to have.
    """
    return Node(b_type, children=children)

def paren(children):
    """
    Return a paren node with the given children.
    
    Parameters:
        children: The children for the paren node to have.
    """
    return bracket(NodeType.PAREN, children)

def unpack_and_wrap_node(node):
    """
    Return either the node's children if it is PAREN or a one-element list of the node.
    
    Parameters:
        node: The node to unpack and wrap.
    """
    if node.node_type is NodeType.PAREN:
        return node.children
    return [node]

BRACKET_DICT = {}
ESCAPE = '`'
WHITESPACE = [' ', '\n', '\t', '\r']

class Bracket:
    """A type of bracket."""
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
    """
    Return the index of the bracket matching the bracket at the given index.
    
    Parameters:
        line: The line to search through.
        ind: The index of the bracket to find a match for.
    """
    start_ind = ind
    
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
            print(' ' * start_ind + 'v')
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
    """
    Return a list containing the tokens in the given line.
    
    Parameters:
        line: The line to tokenize.
    """
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
    """
    Parse a token into a node.
    
    Parameters:
        token: The token to parse.
    """
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
    """
    Return the name of a macro.
    
    Parameters:
        macro: The macro to return the name of.
    """
    return macro.children[0]

def get_form(macro):
    """
    Return the form of a macro.
    
    Parameters:
        macro: The macro to return the form of.
    """
    return macro.children[1].children

def get_product(macro):
    """
    Return the product of a macro.
    
    Parameters:
        macro: The macro to return the product of.
    """
    return macro.children[2].children

def eval_macro(product, mappings, interpreter):
    """
    Evaluate a macro the has already been matched and mapped.
    
    Parameters:
        product: The product form of the macro or a python function (mappings, interpreter -> nodes)
        mappings: The mappings from capture nodes to expressions.
        interpreter: The interpreter to run the macro in.
    """
    if product[0].node_type != NodeType.FUNC: #A normal macro
        prod_result = fill_in_form(product, mappings)
        temp_intp = intp.Interpreter(interpreter.mcs_product) #No side effects if BALK
        evaluated = temp_intp.interpret_nodes(prod_result)[0] #The first should be either BALK or a PAREN
            
        if evaluated != normal('BALK'):
            evaluated = evaluated.children #Unwrap
            interpreter.set_mcs_product(temp_intp.mcs_product) #Now side effects take place
            return True, evaluated
        else:
            return False, None
    else: #product is a Python function (mappings, interpreter -> nodes). A built-in macro.
        return product[0](mappings, interpreter)
    
not_match = False, {}
def matches(nodes, form, mappings=None, exact=False): #Return boolean and mappings
    """
    Return whether the form matches the nodes and the mappings if it does.
    
    Parameters:
        nodes: The nodes the check for a match.
        form: The form of the macro.
        mappings: The mappings to start with.
        exact: Whether nodes has to match form exactly or just contain a sublist that does
    """
    mappings = mappings if mappings else {} #Initialize mappings
    
    m_len = len(form)
    
    if len(nodes) < m_len: #nodes is too short
        return not_match
    
    if exact and len(nodes) > m_len:
        return not_match
    
    for i in range(0, m_len):
        n = nodes[i] #nodes is at least as long as form
        m = form[i]
        
        #If the node has already been captured, check identity. Otherwise capture.
        if m.node_type is CAPTURE:
            m_key = get_key(m)
            if m_key in mappings:
                captured = mappings[m_key]
                if n != captured:
                    return not_match
            else:
                mappings[m_key] = n
        #Check if the children exactly match. Also, the bracket type must be the same.
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