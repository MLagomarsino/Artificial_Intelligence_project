from planner import plan
from planner import encoder
from planner.plan import Plan
import utils

from CDCL_solver.formula import Formula
from CDCL_solver.cdcl import Solver
from CDCL_solver.heuristics import RandomHeuristic

from formula import FormulaMgr, NnfConversion, CnfConversion


class Search():
    def __init__(self, encoder, initial_horizon):
        self.encoder = encoder
        self.horizon = initial_horizon
        self.found = False


class LinearSearch(Search):

    def do_search(self):

        print('Start linear search')
        # Implement linear search here and return a plan

        while True:

            mgr = FormulaMgr()

            # Translate the plan in a propositional formula
            planning_formula = self.encoder.encode(self.horizon)


            planning_formula.do_print()

            # Conversion to NNF (Negative Normal Form)
            nnf = NnfConversion(mgr)
            formula_nnf = nnf.do_conversion(planning_formula)

            # Conversion to CNF (Conjunctive Normal Form)
            cnf = CnfConversion(mgr)
            formula_cnf = cnf.do_conversion(formula_nnf)
            """

            # Solve the built formula using CDCL solver (Random Heuristic)
            #h = RandomHeuristic()
            #solution = Solver(formula_cnf, h, True)


            # planning_formula is satisfied
            if solution.run():
                # Create a plan object
                final_plan = Plan(solution, encoder)
                # exit the loop
                break
            """

            # Inverse translation: to a number corresponds action
            # at a certain step

            # Increase horizon
            self.horizon += 1

            print(self.encoder.actions[0].name)

        # Must return a plan object
        # when plan is found
        return final_plan
