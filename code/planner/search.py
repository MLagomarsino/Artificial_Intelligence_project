from planner import plan
from planner import encoder
from planner.plan import Plan
import utils

from CDCL_solver.formula import Formula
from CDCL_solver.cdcl import Solver
from CDCL_solver.heuristics import RandomHeuristic, PureMomsHeuristic

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

        mgr = FormulaMgr()

        while True:

            final_formula = Formula()
            # Translate the plan in a propositional formula
            planning_formula = self.encoder.encode(self.horizon)

            #planning_formula.do_print()

            # Conversion to NNF (Negative Normal Form)
            nnf = NnfConversion(mgr)
            formula_nnf = nnf.do_conversion(planning_formula)

            # Conversion to CNF (Conjunctive Normal Form)
            formula_cnf = CnfConversion(mgr)
            formula_cnf.do_conversion(formula_nnf)

            #print(formula_cnf.get_clauses())

            # TODO
            final_formula.set_cnf(self.encoder.inverse.__len__(), [[45,46],[56,50]])# formula_cnf.clauses)

            # Solve the built formula using CDCL solver (Random Heuristic)
            h = PureMomsHeuristic(True)
            s = Solver(final_formula, h, True)

            solution = s.run()

            if not solution:
                # Increase horizon
                self.horizon += 1

            else:
                # A plan is found
                print("\nThe PLAN is found!")

                # Create a Plan object
                problem_plan = Plan(solution, self.encoder)

                problem_plan.do_print()
                break

        # Return a plan object
        return problem_plan
