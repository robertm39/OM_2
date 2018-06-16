# -*- coding: utf-8 -*-
"""
Created on Fri Jun 15 12:52:58 2018

@author: rober
"""

from node import Node, NodeType
import om_2_utils as utils
from om_2_utils import key_from_name as kfn

PAREN = NodeType.PAREN
FUNC = NodeType.FUNC


def get_macro(name, form, product):
    return utils.bracket(PAREN, [name,
                                 form,
                                 product])

def get_func_macro(name_exp, form_exp, func, func_name):
    name = utils.parse(name_exp)
    form = utils.parse(form_exp)
    func_node = Node(FUNC, val=func_name, func=func)
    product = utils.paren([func_node])
    return get_macro(name, form, product)
###############################################################################
def unw_product(mappings, interpreter):
    l = mappings[kfn('l')]
    return True, l.children

def unw_macro():
    return get_func_macro('unw', '(unw  ~l)', unw_product, 'unw_product')
###############################################################################
def tail_product(mappings, interpreter):
    l = mappings[kfn('l')]
    tail = l.children[1:]
    return True, [utils.paren(tail)]

def tail_macro():
    return get_func_macro('tail', '(tail ~l)', tail_product, 'tail_product')
###############################################################################
def head_product(mappings, interpreter):
    l = mappings[kfn('l')]
    head = l.children[0]
    return True, [head]
    
def head_macro():
    return get_func_macro('head', '(head ~l)', head_product, 'head_product')
###############################################################################
def set_mcs_product(mappings, interpreter):
    new_mcs = mappings[kfn('a')]
    interpreter.set_mcs_product(new_mcs)
    return True, []

def set_mcs_macro():
    return get_func_macro('set-mcs', '(set-mcs ~a)', set_mcs_product, 'set_mcs_product')
###############################################################################
def get_builtin_macros():
    macros = [unw_macro(),
              tail_macro(),
              head_macro(),
              set_mcs_macro()]
    return utils.paren([utils.bracket(PAREN, macros)])