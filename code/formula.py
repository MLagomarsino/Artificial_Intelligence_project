#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon May 20 22:37:49 2019

@author: tac
"""
from __future__ import print_function

from enum import Enum


class Operator(Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    IMP = "IMP"
    IFF = "IFF"


class Node:

    def __init__(self, node_id, op=None, left=None, right=None, label=None):
        self.id = node_id  # Unique node id
        self.op = op  # None if it is a variable
        self.left = left  # left operand
        self.right = right  # right operand
        self.label = label  # an optional label (could be handy for encodings)
        if left is not None:
            left.refcount += 1
        if right is not None:
            right.refcount += 1
        self.refcount = 0  # reference count for garbage collection

    # Variables (op == None) are hashed according to their id
    # Expressions (op != None) are hashed according to children and operator
    # This enables subformula sharing
    def __hash__(self):
        base = 17
        if self.op is None:
            base = 31 * base + hash(self.id)
        else:
            base = 31 * base + hash(self.op)
        if self.left is not None:
            base = 31 * base + hash(self.left.id)
        if self.right is not None:
            base = 31 * base + hash(self.right.id)
        return base

    # Variables (op == None) are equal when they have the same id
    # Epressions (op != None) are equal according to children and operator
    def __eq__(self, other):
        result = self.__class__ == other.__class__
        if self.op is None:
            return result and self.id == other.id
        else:
            return result and \
                   self.op == other.op and \
                   self.left.id == other.left.id and \
                   (self.right is None or self.right.id == other.right.id)

    def do_print(self, print_id=False, print_label=False):
        # Internal function to prinr IDs
        def get_id(i, flag):
            if flag:
                return ":" + str(i)
            else:
                return ""

        if self.op is None:
            if print_label and self.label is not None:
                print(str(self.label), end=' ')
            else:
                print("v" + str(self.id), end=' ')
        else:
            print("(" + self.op.name + get_id(self.id, print_id), end=' ')
            if self.left is not None:
                self.left.do_print(print_id, print_label)
            print("", end=' ')
            if self.right is not None:
                self.right.do_print(print_id, print_label)
            print(")", end=' ')


class FormulaMgr:

    def __init__(self):
        self.lastId = 0
        self.recycleIds = list()  # When deleting a node, recycle the unique id
        self.node2id = dict()  # Get node id from node
        self.id2node = list()  # Get node from node id
        self.id2node.append(None)
        self.name2id = dict()  # Get node id from label (labels must be unique)

    # Get a new id or recycle one
    def getId(self):
        if len(self.recycleIds) == 0:
            self.id2node.append(None)
            self.lastId += 1
            return self.lastId
        else:
            return self.recycleIds.pop()

    # Dispose of a node when its reference count reaches 1
    # or reduce its reference count
    def dispose(self, node):
        if node.refcount > 1:
            node.refcount -= 1
        else:
            # Reduce the reference count of the children (if any)
            if node.left is not None:
                self.dispose(node.left)
            if node.right is not None:
                self.dispose(node.right)
            # If the node has a label, remove it from the index
            if node.label is not None:
                self.name2id.pop(node.label)
            # Remove the node from all other indexes
            self.node2id.pop(node)
            self.id2node[node.id] = None
            # The id can be recycled
            self.recycleIds.append(node.id)

    # Make a variable. The id is assigned by the manager, the
    # label can be chosen by the user. The label must be unique
    def mkVar(self, name=None):
        if name is not None:
            node_id = self.name2id.get(name)
            if node_id is not None:
                return self.id2node[node_id]
        node_id = self.getId()
        node = Node(node_id, label=name)
        self.node2id[node] = node_id
        self.id2node[node_id] = node
        if name is not None:
            self.name2id[name] = node_id
        return node

    # Get the variable node using the label as a reference
    def getVarByName(self, name):
        if name is not None:
            return self.id2node[self.name2id.get(name)]
        else:
            return None

    # Get the variable node using the unique id as a reference
    def getVarById(self, varid):
        if varid <= self.lastId:
            return self.id2node[varid]
        else:
            return None

    def mkOp(self, temp):
        nodeid = self.node2id.get(temp)
        if nodeid is not None:
            # If the subformula was already created, share it
            node = self.id2node[nodeid]
            node.refcount += 1
            return node
        else:
            # Create a new subformula node
            nodeid = self.getId()
            temp.id = nodeid
            self.id2node[nodeid] = temp
            self.node2id[temp] = nodeid
        return temp

    def mkAnd(self, f, g):
        temp = Node(0, op=Operator.AND, left=f, right=g)
        return self.mkOp(temp)

    def mkOr(self, f, g):
        temp = Node(0, op=Operator.OR, left=f, right=g)
        return self.mkOp(temp)

    def mkNot(self, f):
        temp = Node(0, op=Operator.NOT, left=f)
        return self.mkOp(temp)

    def mkImply(self, f, g):
        temp = Node(0, op=Operator.IMP, left=f, right=g)
        return self.mkOp(temp)

    # Operator for working with lists (Recursive function)
    def mkOpArray(self, lit_list, op):
        assert (len(lit_list) != 0)
        # Save the length of the list
        len_list = len(lit_list)
        if len_list == 1:
            return lit_list[0]
        # Create a balanced tree
        left_half = self.mkOpArray(lit_list[0:len_list / 2], op)
        right_half = self.mkOpArray(lit_list[len_list / 2:len_list], op)
        temp = Node(0, op=op, left=left_half, right=right_half)
        return self.mkOp(temp)

    # List of variables (output_list) from a list of literals (input_list)
    def mkVarArray(self, input_list):
        assert (len(input_list) != 0)

        output_list = []
        for lit in input_list:
            # Check if negative
            if lit < 0:
                # Create variable and negate it
                output_list.append(self.mkNot(self.mkVar(-lit)))
            else:
                output_list.append(self.mkVar(lit))
        return output_list

    # AND among all the elements in the lit_list
    def mkAndArray(self, lit_list):
        return self.mkOpArray(lit_list, Operator.AND)

    # OR among all the elements in the lit_list
    def mkOrArray(self, lit_list):
        return self.mkOpArray(lit_list, Operator.OR)


class NnfConversion:

    def __init__(self, mgr):
        self.manager = mgr

    def do_conversion(self, node):
        if node.op is not None:
            if node.op == Operator.NOT:
                temp = self.convert(node.left, -1)
                self.manager.dispose(node)
                node = temp
            else:
                node = self.convert(node, 1)
        return node

    def convert(self, node, polarity):
        if node.op is None:
            if polarity > 0:
                return node
            else:
                return self.manager.mkNot(node)
        if node.op == Operator.NOT:
            temp = self.convert(node.left, -1 * polarity)
            self.manager.dispose(node)
            return temp
        elif node.op == Operator.AND:
            if polarity < 0:
                left = self.convert(node.left, -1)
                right = self.convert(node.right, -1)
                return self.manager.mkOr(left, right)
            else:
                left = self.convert(node.left, 1)
                right = self.convert(node.right, 1)
                return self.manager.mkAnd(left, right)
        elif node.op == Operator.OR:
            if polarity < 0:
                left = self.convert(node.left, -1)
                right = self.convert(node.right, -1)
                return self.manager.mkAnd(left, right)
            else:
                left = self.convert(node.left, 1)
                right = self.convert(node.right, 1)
                return self.manager.mkOr(left, right)
        elif node.op == Operator.IMP:
            if polarity < 0:
                left = self.convert(node.left, 1)
                right = self.convert(node.right, -1)
                return self.manager.mkAnd(left, right)
            else:
                left = self.convert(node.left, 1)
                right = self.convert(node.right, 1)
                return self.manager.mkImply(left, right)
        else:
            # This cannot happen
            assert True


class CnfConversion:

    def __init__(self, mgr):
        self.clauses = list()
        self.definitions = dict()
        self.manager = mgr

    # Assumes that the formula is in negative normal form
    def do_conversion(self, node):
        # Fail if the formula is not in NNF
        assert (node.op != Operator.NOT) or (node.left.op is None)

        # Add the unit clause representing the formula itself
        self.clauses.append([node.id])
        if node.op is not None:
            self.convert(node)
        return

    def get_clauses(self):
        return self.clauses

    def convert(self, node):
        # Fail if the formula is not in NNF
        assert (node.op != Operator.NOT) or (node.left.op is None)
        # Nothing to do if a literal is reached (variable or negation thereof) 
        if (node.op is None) or (node.op == Operator.NOT):                         #MARTAAAA
            return
        # An operator: AND, OR, IMP: add the definitions and propagate 
        # If the subformula was already visited, no need to visit again
        self.add_definitions(node)
        if self.definitions.get(node.left.id) is None:
            self.convert(node.left)
        if self.definitions.get(node.right.id) is None:
            self.convert(node.right)

    def add_definitions(self, node):
        def_clauses = list()
        # Local alias for negation function
        neg = self.neg
        # The literal corresponding to the formula
        l = node.id
        # The literal corresponding to the left operand
        # Negations must be applied to variables only
        if node.left.op == Operator.NOT:
            assert (node.left.left.op is None)
            l1 = neg(node.left.left.id)
        else:
            l1 = node.left.id
        # The literal corresponding to the right operand
        # Negations must be applied to variables only
        if node.right.op == Operator.NOT:
            assert (node.right.left.op is None)
            l2 = neg(node.right.left.id)
        else:
            l2 = node.right.id
        if node.op == Operator.AND:
            def_clauses.append([l, neg(l1), neg(l2)])
            def_clauses.append([neg(l), l1])
            def_clauses.append([neg(l), l2])
        elif node.op == Operator.OR:
            def_clauses.append([neg(l), l1, l2])
            def_clauses.append([l, neg(l1)])
            def_clauses.append([l, neg(l2)])
        elif node.op == Operator.IMP:
            def_clauses.append([neg(l), neg(l1), l2])
            def_clauses.append([l, l1])
            def_clauses.append([l, neg(l2)])
        else:
            # This cannot happen
            assert False
        self.definitions[node.id] = def_clauses
        self.clauses.extend(def_clauses)

    def neg(self, id):
        return int(id * -1)
