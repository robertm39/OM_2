# -*- coding: utf-8 -*-
"""
Created on Fri Jun 15 12:52:58 2018

@author: rober
"""

from node import Node, NodeType, BRACKET_TYPES
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

def wrap_bin_func(mappings, bin_func):
    try:
        return (True, [utils.normal(str(bin_func(get(mappings, 'a'), get(mappings, 'b'))))])
    except ValueError:
        return False, []

def get_binary_macro(sign, bin_func):
#    func = lambda mappings, interpreter: (True, [utils.normal(str(bin_func(get(mappings, 'a'), get(mappings, 'b'))))])
    func = lambda mappings, interpreter: wrap_bin_func(mappings, bin_func)
    return get_func_macro(sign, '(~a ' + sign + ' ~b)', func, sign + '_product')

def get(mappings, name):
    return mappings[kfn(name)]
###############################################################################
def ind_product(mappings, interpreter):
    i = get(mappings, 'i')
    l = get(mappings, 'l')
    node = l.children[int(i.val)]
    return True, [node]

def ind_macro():
    return get_func_macro('ind', '(ind ~i ~l)', ind_product, 'ind_product')
###############################################################################
def loc_product(mappings, interpreter):
    def make_local(nodes, node_id, prog): #Modifies the passed object
        for v_node in nodes:
            for node in prog:
                if node.node_type is NodeType.NORMAL:
                    if node.val == v_node.val:
                        if node.id == v_node.id:
                            node.id = node_id #Make into a local node
                if node.node_type in BRACKET_TYPES:
                    make_local([v_node], node_id, node.children)
    
    node_id = interpreter.take_id()
    nodes = get(mappings, 'v').children
    prog = get(mappings, 'p').children
    prog = [n.copy() for n in prog]
    make_local(nodes, node_id, prog)
    return True, prog

def loc_macro():
    return get_func_macro('loc', '(loc ~v ~p)', loc_product, 'loc_product')
###############################################################################
def cntr_product(mappings, interpreter):
    l = get(mappings, 'l')
    name = ''.join([node.val for node in l.children])
    return True, [utils.normal(name)]

def cntr_macro():
    return get_func_macro('cntr', '(cntr ~l)', cntr_product, 'cntr_product')
###############################################################################
def expd_product(mappings, interpreter):
    a = get(mappings, 'a')
    return True, [utils.normal(c) for c in a.val]

def expd_macro():
    return get_func_macro('expd', '(expd ~a)', expd_product, 'expd_product')
###############################################################################
def unw_product(mappings, interpreter):
    l = get(mappings, 'l')
    return True, l.children

def unw_macro():
    return get_func_macro('unw', '(unw  ~l)', unw_product, 'unw_product')
###############################################################################
def tail_product(mappings, interpreter):
    l = get(mappings, 'l')
    tail = l.children[1:]
    return True, [utils.paren(tail)]

def tail_macro():
    return get_func_macro('tail', '(tail ~l)', tail_product, 'tail_product')
###############################################################################
def head_product(mappings, interpreter):
    l = get(mappings, 'l')
    if l.children:
        head = l.children[0]
        return True, [head]
    return True, [] #The macro still works, but it's empty
    
def head_macro():
    return get_func_macro('head', '(head ~l)', head_product, 'head_product')
###############################################################################
def set_mcs_product(mappings, interpreter):
    new_mcs = get(mappings, 'a')
    interpreter.set_mcs_product(new_mcs)
    return True, []

def set_mcs_macro():
    return get_func_macro('set-mcs', '(set-mcs ~a)', set_mcs_product, 'set_mcs_product')
###############################################################################
def get_builtin_macros():
    macros = [ind_macro(),
              loc_macro(),
              cntr_macro(),
              expd_macro(),
              unw_macro(),
              tail_macro(),
              head_macro(),
              set_mcs_macro(),
              get_binary_macro('+', lambda a, b: float(a.val) + float(b.val)),
              get_binary_macro('-', lambda a, b: float(a.val) - float(b.val)),
              get_binary_macro('*', lambda a, b: float(a.val) * float(b.val)),
              get_binary_macro('/', lambda a, b: float(a.val) / float(b.val)),
              get_binary_macro('//', lambda a, b: float(a.val) // float(b.val)),
              get_binary_macro('**', lambda a, b: float(a.val) ** float(b.val)),
              get_binary_macro('%', lambda a, b: float(a.val) % float(b.val)),
              get_binary_macro('>', lambda a, b: float(a.val) > float(b.val)),
              get_binary_macro('>=', lambda a, b: float(a.val) >= float(b.val)),
              get_binary_macro('<', lambda a, b: float(a.val) < float(b.val)),
              get_binary_macro('<=', lambda a, b: float(a.val) <= float(b.val)),
              get_binary_macro('f-eq', lambda a, b: float(a.val) == float(b.val)),
              get_binary_macro('f-neq', lambda a, b: float(a.val) != float(b.val))]
    return utils.paren([utils.bracket(PAREN, macros)])