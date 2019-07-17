#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 15:32:56 2019

@author: tac
"""
from cdcl import Status
import random


class RandomHeuristic:

    def __init__(self):
        pass

    def run(self, formula, stack):
        if formula.open_var > 1:
            num = random.randint(1, formula.open_var)
        else:
            num = 1
        for var_index in range(1, len(formula.variable_list)):
            v = formula.variable_list[var_index]
            if v.value == 0:
                num = num - 1
                if num == 0:
                    value = [-1, 1][random.randint(0, 1)]
                    formula.do_eval(var_index, value)
                    # The reason of a choice is empty
                    stack.append(Status(var_index, False, None))
                    break
        return


class PureMomsHeuristic:

    def __init__(self, do_pure):
        self.do_pure = do_pure
        random_heur = RandomHeuristic()
        self.choose_at_random = random_heur.run

    def count_occurrences(self, formula, occ_list):
        total = occ2 = occ3 = 0
        for cl_index in occ_list:
            cl = formula.clause_list[cl_index]
            if cl.subsumer == 0:
                total += 1
            if cl.open == 2:
                occ2 += 1
            elif cl.open == 3:
                occ3 += 1
        return total, occ2, occ3

    def update_best_and_sign(self, pos, neg, v_index, max_score, best, sign):
        if (pos * neg) > max_score:
            max_score = pos * neg
            best = v_index
            if pos > neg:
                sign = -1
            else:
                sign = 1
        return max_score, best, sign

    def run(self, formula, stack):
        assert formula.open_var > 0
        pure_lits = list()
        max_2 = max_3 = 0;
        best_2 = best_3 = 0;
        sign_2 = sign_3 = 0;
        for var_index in range(1, len(formula.variable_list)):
            v = formula.variable_list[var_index]
            if v.value == 0:
                pos, pos_2, pos_3 = self.count_occurrences(formula, v.pos_lits)
                neg, neg_2, neg_3 = self.count_occurrences(formula, v.neg_lits)
                if (neg == 0) and (pos != 0):
                    # A pure positive literal was found
                    pure_lits.append(var_index)
                elif (pos == 0) and (neg != 0):
                    # A pure negative literal was found
                    pure_lits.append(-1 * var_index)
                elif (pos != 0) and (neg != 0):
                    max_2, best_2, sign_2 = self.update_best_and_sign(pos_2, neg_2, var_index, max_2, best_2, sign_2)
                    max_3, best_3, sign_3 = self.update_best_and_sign(pos_3, neg_3, var_index, max_3, best_3, sign_3)
        if self.do_pure and (len(pure_lits) > 0):
            for lit in pure_lits:
                formula.do_eval(abs(lit), lit / abs(lit))
                # Pure literal becomes simply a preference in the heuristics
                # The reason of a choice is empty
                stack.append(Status(abs(lit), False, None))
        elif best_2 != 0:
            # If there were no pure literals, and some binary clauses were found
            # choose most occurring literal in there
            formula.do_eval(best_2, sign_2)
            # The reason of a choice is empty
            stack.append(Status(best_2, False, None))
        elif best_3 != 0:
            # If there were no pure literals, no binary clauses, but some ternary clauses were found
            # choose most occurring literal in there
            formula.do_eval(best_3, sign_3)
            # The reason of a choice is empty
            stack.append(Status(best_3, False, None))
        else:
            # If there are no open binary or ternary clauses, choose at random
            self.choose_at_random(formula, stack)
        return

# ADDED Simple VSIDS heuristic
class VsidsHeuristic:

    def __init__(self, period):
        self.priority = list()
        self.period = period
        self.invocations = 0

    def run(self, formula, stack):
        self.invocations += 1
        if self.invocations == 1:
            # At the first invocations, randomize the priorities
            self.priority = list(range(len(formula.variable_list)))
            random.shuffle(self.priority)
        if self.invocations % self.period == 0:
            # print("## Invocation: ", self.invocations)
            # for i in range(len(formula.conflict_list)):
            #    print (i, " pos: ", formula.conflict_list[i].pos, " neg: ", formula.conflict_list[i].neg)
            # Each 'period' invocations change priorities according to conflicts
            self.priority = \
                sorted(range(len(formula.variable_list)),
                       key=lambda x: formula.conflict_list[x].pos + formula.conflict_list[x].neg)
        # Choose variable with maximum priority
        for var in self.priority[::-1]:
            if (var != 0) and (formula.variable_list[var].value == 0):
                if formula.conflict_list[var].pos < formula.conflict_list[var].neg:
                    formula.do_eval(var, 1)
                else:
                    formula.do_eval(var, -1)
                stack.append(Status(var, False, None))
                break
