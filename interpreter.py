# -*- coding: utf-8 -*-
"""
Created on Mon May 21 17:24:38 2018

@author: rober
"""

import om_2_utils as utils
import om_2_builtin_macros as builtin_macros
from node import NodeType

NORMAL, CAPTURE, PAREN, SQUARE, CURLY, = NodeType.NORMAL, NodeType.CAPTURE, NodeType.PAREN, NodeType.SQUARE, NodeType.CURLY

INTERPRETED_BRACKETS = (SQUARE, CURLY)

def is_macro(node):
    """
    Return whether node is a macro.
    
    Parameters:
        nodes: The node to check for being a macro.
    """
    if node.node_type is PAREN:
        if len(node.children) == 3:
            name, form, product = node.children
            return name.node_type in [NORMAL, CAPTURE] and form.node_type is PAREN and product.node_type is PAREN
        else:
            return False
    else:
        return False

class Interpreter:
    """An interpreter that interprets om2 expressions."""
    def __init__(self, mcs_product=None):
        self.mcs_product = None
        self.set_mcs_product(mcs_product if mcs_product else builtin_macros.get_builtin_macros())
        self.id = 1
    
    def take_id(self):
        """Return a unique id."""
        result = self.id
        self.id += 1
        return result
    
    def get_mcs_macro(self):
        """Return the macro space macro, or the mcs macro."""
        return utils.bracket(PAREN, children=[utils.normal('mcs'),
                                              utils.bracket(PAREN, [utils.normal('mcs')]),
                                              utils.bracket(PAREN, #Do need both unwraps
                                                            [utils.bracket(PAREN, 
                                                                           [self.mcs_product])])])
    
    def set_mcs_product(self, mcs_product):
        """
        Set the macro space macro product.
        
        Parameters:
            mcs_product: The product to set the mcs macro's product to.
        """
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
        """Sort the macros."""
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
        """
        Return the line, parsed into an om2 expression.
        
        Parameters:
            line: The line to parse.
        """
        tokens = utils.tokenize(line)
        result = [utils.parse(token) for token in tokens]
        return result
    
    def interpret(self, line):
        """
        Interpret the line.
        
        Parameters:
            line: The line to interpret.
        """
        nodes = self.get_parsed(line)
        return self.interpret_nodes(nodes)
        
    def interpret_nodes(self, nodes, level=0):
        """
        Interpret the nodes.
        
        Parameters:
            nodes: The nodes to interpret.
            level: The recursion level. For debugging.
        """
#        p_nodes = nodes[:]
#        nodes = self.interpret_step(nodes) #Evaluate one macro or bracket
        going = True
        while going:
#            p_nodes = nodes
            going, nodes = self.interpret_step(nodes, level=level)
            
        return nodes
    
    def interpret_step(self, nodes, level=0): #level for debugging
        """
        Interpret the given nodes for one step.
        
        Parameters:
            nodes: The nodes to interpret.
            level: The recursion level. For debugging.
        """
        
        #Story time:
        #
        #I used to have a try-catch block instead of this if-else block
        #(don't ask why, I have no idea why I did that)
        #I would do
        #   fib_i = min([i for i in range(0, len(nodes)) if nodes[i].node_type in INTERPRETED_BRACKETS])
        #and catch the ValueError if there were no brackets to interpret.
        #
        #But when I tried to run
        #   (set a [a + 1]) while (a < 5)
        #
        #the while macro turned (a < 5) into [unw (a < 5)]
        #and because larger macros are executed first, the < macro
        #tried to compare a to 5 before evaluating a to a number,
        #it threw a ValueError. This sent the code to the second part
        #of the try-catch block, acting as if there were no brackets to
        #interpret. It took me a while to catch this error. 
        #
        #Moral of the story:
        #don't use exception handling for normal control flow.
        #(unless you really, really have to, or you're writing in Perl.)
        #
        #Also, remember to use square brackets whenever you need a smaller
        #macro to evaluate before a larger one.
        
        bracket_indexes = [i for i in range(0, len(nodes)) if nodes[i].node_type in INTERPRETED_BRACKETS]
        if bracket_indexes:
            #The first interpreted bracket index
            fib_i = min(bracket_indexes)
            bracket = nodes[fib_i]
            bracket_result = self.interpret_nodes(bracket.children, level=level+1) #A list of nodes
            if bracket.node_type is CURLY: #Wrap in a PAREN
                bracket_result = [utils.bracket(PAREN, bracket_result)]
            
            result = nodes[:fib_i] + bracket_result + nodes[fib_i+1:] #Replace the bracket with the result
            return True, result
        else:
            changed, n_nodes = self.apply_one_macro(nodes) #Apply one macro
            if changed:
                return True, n_nodes
            else:
                return False, nodes
    
    def apply_one_macro(self, nodes):
        """
        Apply the first matching macro to nodes.
        
        Parameters:
            nodes: The nodes to apply a macro to.
        """
        for macro in self.macros: #self.macros MUST be sorted
            matched, new_nodes = self.apply_macro(nodes, macro)
            if matched:
                return True, new_nodes
            
        return False, None
    
    def apply_macro(self, nodes, macro):
        """
        Apply the given macro to the nodes.
        
        Parameters:
            nodes: The nodes to apply the macro to.
            macro: The macro to apply to the nodes.
        """
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