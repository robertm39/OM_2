# -*- coding: utf-8 -*-
"""
Created on Fri May  4 12:16:39 2018

@author: rober
"""

import om
from om_2.utils import fill_in_form, get_key

class Macro:
    def __init__(self,
                 form,
                 get_product=None,
                 product_form=None,
                 cond_form=None,
                 shell=None,
                 name='unknown macro'):
        self.form = form
        self.ln = len(form)
        self.name=name
        self.is_cond = cond_form != None
        
        if get_product != None:
            self.get_product = get_product
        elif product_form != None:
            self.get_product = lambda mappings: fill_in_form(product_form, mappings)
        else:
            raise AssertionError('No get_product or product_form')
    
    def __str__(self):
        return self.name
    
    def __lt__(self, other): #Less than -> runs earlier
        if self.ln > other.ln:
            return True
        if self.ln < other.ln:
            return False
        if self.time_added > other.time_added:
            return True
        return False
    
    #Whether this macro matches the given expression, starting at the left
    def matches(self, expr, norm_done=False, form=None, mappings=None, exact=False):
        form = self.form if form == None else form
        mappings = {} if mappings == None else mappings #Captured values: name -> node
        i = 0
        
        not_matches = False, {}, 0
        
        if len(expr) < len(form):
            return not_matches
        
        #For an exact match, the expr and the form must be the same length
        if exact and len(expr) > len(form):
            return not_matches
        
        for node in expr:
            f_node = form[i]
            
            if f_node.node_type is om.NodeType.CAPTURE: #Capture nodes
                key = get_key(f_node)
                if key in mappings: #See whether the node matches the captured node
                    captured_node = mappings[key]
                    if node != captured_node:
                        return not_matches
                else: #Capture this node
                    mappings[key] = node
            elif f_node.node_type in om.BRACKET_TYPES: #A list
                if f_node.node_type != node.node_type:
                    return not_matches
                does_match, mappings, length = self.matches(node.children,
                                                            form=f_node.children,
                                                            mappings=mappings,
                                                            exact=True)
                if not does_match:
                    return not_matches
            elif not norm_done:
                if f_node != node:
                    return not_matches
            i += 1
            if i >= len(form):
                break #We've gone past the form
        
        return True, mappings, len(form)