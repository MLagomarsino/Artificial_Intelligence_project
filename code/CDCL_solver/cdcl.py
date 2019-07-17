#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 11:32:47 2017

@author: tac
"""


# MODIFIED: keep track of reasons
class Status:
    def __init__(self, var_index, closed, clause):
        self.var_index = var_index
        self.closed = closed
        self.reason = clause


class Solver:
    def __init__(self, formula, heuristic, do_trace=False):
        self.formula = formula
        self.choose_variable = heuristic
        self.do_trace = do_trace
        self.stack = list()

    def run(self):
        done = False
        formula = self.formula
        while (not done):
            # Assign all unit clauses, including those that are generated by this process
            self.unit_propagate()
            if formula.is_satisfied():
                # The formula is satisfied: end of search
                done = True
            elif formula.is_contradicted():
                # The formula is contradicted: keep searching if possible, otherwise give up
                done = self.backtrack()
            else:
                # We must choose a variable and assign it tentatively
                self.choose_variable.run(formula, self.stack)
                self.trace("SPLIT on:", self.stack[-1].var_index)
        return self.extract_assignment()

    def unit_propagate(self):
        formula = self.formula
        stack = self.stack
        # While there is at least one unit clause...
        while (len(formula.unit_cl_list) > 0):
            # ... get the unit clause 
            cl_index = formula.unit_cl_list.pop()
            cl = formula.clause_list[cl_index]
            for lit in cl.lit_list:
                # Search the variable still unassigned (if any)
                var = formula.variable_list[abs(lit)]
                if (var.value == 0):
                    # Assign the variable so as to subsume the clause
                    formula.do_eval(abs(lit), lit / abs(lit))
                    # Record the assignemnt in the stack as "closed"
                    # ADDED: Add the reason for this assignment (the unit)
                    stack.append(Status(abs(lit), True, cl))
                    self.trace("UNIT on:", lit, " with reason ", cl.lit_list)
                    break
        return

    # MODIFIED: simple conflict-driven backjumping and learning
    def backtrack(self):
        formula = self.formula
        stack = self.stack
        # Initialize the working reason
        wr = self.init_working_reason(formula)
        # Reset the empty clause list
        formula.empty_cl_list = list()
        # Go back in the stack, search for an "open" assigment
        while (len(stack) > 0):
            sr = stack.pop()
            # Get the variable index
            var_index = sr.var_index
            self.trace("RETRACT: ", var_index * formula.variable_list[var_index].value)
            # If the variable caused the conflict, resolve its reason
            # with the working reason to obtain a new working reason
            if (var_index in wr):
                self.update_working_reason(wr, sr.reason, formula)
            # Undo the old assignment
            formula.undo_eval(var_index)
            if (not sr.closed):
                # The branch literal is in the working reason
                if (var_index in wr):
                    # Add the working reason as a new clause
                    # Unit propagation will take care of the assignment
                    lits = self.extract_lits_from_working_reason(wr)
                    formula.add_clause(lits)
                    # The number of open clauses does not change
                    # because this clause is implied
                    self.trace("BACKTRACK on: ", var_index)
                    return False
                else:
                    self.trace("SKIP: ", var_index)
                # If the branch literal is not in the working
                # reason it is irrelevant for the current conflict
        # end of while 

        # No further backtracking is possible: the search must end
        return True

    def extract_assignment(self):
        assignment = list()
        for sr in self.stack:
            value = self.formula.variable_list[sr.var_index].value
            assignment.append(sr.var_index * value)
        return assignment

    def init_working_reason(self, formula):
        formula = self.formula
        wr = dict()
        cl_index = formula.empty_cl_list.pop()
        cl = formula.clause_list[cl_index]
        for lit in cl.lit_list:
            wr[abs(lit)] = abs(lit) / lit
            if lit > 0:
                formula.conflict_list[abs(lit)].pos += 1
            else:
                formula.conflict_list[abs(lit)].neg += 1
        self.trace("INIT working reason:", self.extract_lits_from_working_reason(wr))
        return wr

    def update_working_reason(self, wr, clause, formula):
        # Do not consider empty reasons (branches)
        if (clause == None):
            return
        # Resolution between the current working reason and 'clause"
        lits = clause.lit_list
        self.trace("UPDATE working reason with clause:", lits)
        for lit in lits:
            var = abs(lit)
            if var not in wr:
                # The literal is not in the wr, so it should be added
                wr[var] = var / lit
                if (lit > 0):
                    formula.conflict_list[var].pos += 1
                else:
                    formula.conflict_list[var].neg += 1
            else:
                # The literal is in the wr: what to do?
                wr_lit = wr[var] * var
                if (wr_lit * lit < 0):
                    # The literal is resolved and should be removed from wr
                    wr.pop(abs(lit))
        self.trace("NEW working reason:", self.extract_lits_from_working_reason(wr))
        return wr

    def extract_lits_from_working_reason(self, wr):
        lits = list()
        for var, sign in wr.items():
            lits.append(int(var * sign))
        return lits

    def trace(self, *args):
        if self.do_trace:
            print(args)
