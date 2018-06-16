# -*- coding: utf-8 -*-
"""
Created on Mon May 21 17:24:38 2018

@author: rober
"""

import om_2_utils as utils
import om_2_builtin_macros as builtin_macros
#import om_2.node as node
from node import NodeType

NORMAL, CAPTURE, PAREN, SQUARE, CURLY, = NodeType.NORMAL, NodeType.CAPTURE, NodeType.PAREN, NodeType.SQUARE, NodeType.CURLY

INTERPRETED_BRACKETS = (SQUARE, CURLY)

def is_macro(node):
#    print('calling is_macro')
#    print(node)
    if node.node_type is PAREN:
#        print('is_paren')
        if len(node.children) == 3:
#            print('three children')
            name, form, product = node.children
            return name.node_type in [NORMAL, CAPTURE] and form.node_type is PAREN and product.node_type is PAREN
        else:
            return False
    else:
        return False

class Interpreter:
    def __init__(self, mcs_product=None):
        self.mcs_product = None
        self.set_mcs_product(mcs_product if mcs_product else builtin_macros.get_builtin_macros())
        self.id = 1
    
    def take_id(self):
        result = self.id
        self.id += 1
        return result
    
    def get_mcs_macro(self):
        return utils.bracket(PAREN, children=[utils.normal('mcs'),
                                              utils.bracket(PAREN, [utils.normal('mcs')]),
                                              utils.bracket(PAREN, #Do need both unwraps
                                                            [utils.bracket(PAREN, 
                                                                           [self.mcs_product])])])
    
    def set_mcs_product(self, mcs_product):
        if self.mcs_product != mcs_product:
            self.mcs_product = mcs_product
            if len(self.mcs_product.children) == 1:
                product = self.mcs_product.children[0].children #Unwrap twice to get inner list
                self.macros = [node for node in product if is_macro(node)] + [self.get_mcs_macro()]
                self.sort_macros()
            else:
                pass
#                print('IMPROPER MCS FORMAT')
    
    def sort_macros(self):
        name_indices = {utils.parse('mcs'):len(self.macros)}
#        print('macro list?')
#        print(self.mcs_product.children[0].children)
#        print('***********')
        for i in range(0, len(self.mcs_product.children[0].children)):
            node = self.mcs_product.children[0].children[i]
            if is_macro(node):
                name_indices[utils.get_name(node)] = i
        
        name_key = lambda macro: name_indices[utils.get_name(macro)] #Secondary sort
        length_key = lambda macro: -len(utils.get_form(macro)) #Primary sort
        
        self.macros.sort(key=name_key) #This works because of stable sorting
        self.macros.sort(key=length_key) #The secondary sort is supposed to go first
    
    def get_parsed(self, line):
        tokens = utils.tokenize(line)
        result = [utils.parse(token) for token in tokens]
        return result
    
    def interpret(self, line):
        nodes = self.get_parsed(line)
        return self.interpret_nodes(nodes)
        
    def interpret_nodes(self, nodes, level=0):
#        p_nodes = nodes[:]
#        nodes = self.interpret_step(nodes) #Evaluate one macro or bracket
        going = True
        while going:
#            p_nodes = nodes
            going, nodes = self.interpret_step(nodes, level=level)
            
        return nodes
    
    def interpret_step(self, nodes, level=0): #level for debugging
        try:
            #The First Interpreted Bracket Index
            fib_i = min([i for i in range(0, len(nodes)) if nodes[i].node_type in INTERPRETED_BRACKETS])
            bracket = nodes[fib_i]
            bracket_result = self.interpret_nodes(bracket.children, level=level+1) #A list of nodes
            if bracket.node_type is CURLY: #Wrap in a PAREN
                bracket_result = [utils.bracket(PAREN, bracket_result)]
            
            result = nodes[:fib_i] + bracket_result + nodes[fib_i+1:] #Replace the bracket with the result
            return True, result
        except ValueError: #If there are no interpreted brackets
            changed, n_nodes = self.apply_one_macro(nodes) #Apply one macro
            if changed:
                return True, n_nodes
            else:
                return False, nodes
    
    def apply_one_macro(self, nodes):
        for macro in self.macros: #self.macros MUST be sorted
            matched, new_nodes = self.apply_macro(nodes, macro)
            if matched:
                return True, new_nodes
            
        return False, None
    
    def apply_macro(self, nodes, macro):
        form = utils.get_form(macro)
        m_len = len(form)
        for i in range(0, len(nodes) - m_len + 1):
            to_match = nodes[i:i+m_len] #A section from nodes as long as the form
#            if utils.get_name(macro).val == 'set-mcs':
#                print('to_match:', to_match)
            match, mappings = utils.matches(to_match, form)
            if match:
#                print('name:', utils.get_name(macro))
                product = utils.get_product(macro)
                fired, p_result = utils.eval_macro(product, mappings, self)
                if fired: #If it didn't balk
                    result = nodes[:i] + p_result + nodes[i+m_len:]
                    return True, result
        
        return False, None