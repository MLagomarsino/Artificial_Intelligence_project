from planner import plan
from planner import encoder
from planner.plan import Plan
import utils

from CDCL_solver.formula import Formula
from CDCL_solver.cdcl import Solver
from CDCL_solver.heuristics import RandomHeuristic, PureMomsHeuristic

from formula import NnfConversion, CnfConversion


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

            final_formula = Formula()

            # Translate the plan in a propositional formula
            planning_formula = self.encoder.encode(self.horizon)

            # Conversion to NNF (Negative Normal Form)
            nnf = NnfConversion(self.encoder.formula_mgr)
            formula_nnf = nnf.do_conversion(planning_formula)

            # Conversion to CNF (Conjunctive Normal Form)
            formula_cnf = CnfConversion(self.encoder.formula_mgr)
            formula_cnf.do_conversion(formula_nnf)

            # Fill the fields of class Formula()
            num_id = formula_cnf.clauses[0][0]
            final_formula.set_cnf(num_id, formula_cnf.clauses)

            # Solve the built formula using CDCL solver (Random Heuristic)
            h = RandomHeuristic()
            s = Solver(final_formula, h)

            solution = s.run()

            # Conversion from id to label
            sol = list()
            for lit in solution:
                # Check if literal appears positive or negative
                sign = lit/abs(lit)
                node = self.encoder.formula_mgr.getVarById(abs(lit))
                if node.op is None:
                    if sign == 1:
                        sol.append(node.label)
                    else:
                        sol.append(-node.label)

            if not sol:
                # Increase horizon
                self.horizon += 1
                print("\nThe PLAN is not found!\nNew horizon: " + str(self.horizon))

            else:
                # A plan is found
                print("\nA PLAN is found, before validating:")

                # Create plan object
                problem_plan = Plan(sol, self.encoder)

                # Print plan
                problem_plan.do_print()
                break

        # Return a plan object
        return problem_plan
