from planner import plan
from planner import encoder
from planner.plan import Plan
import utils

from CDCL_solver.formula import Formula
from CDCL_solver.dpll import Solver
from CDCL_solver.heuristics import RandomHeuristic


class Search():
    def __init__(self, encoder, initial_horizon):
        self.encoder = encoder
        self.horizon = initial_horizon
        self.found = False

class LinearSearch(Search):

    def do_search(self):
        # Override initial horizon (M: estimate the number of actions to reach the goal)
        # self.horizon = 1

        print('Start linear search')
        # Implement linear search here and return a plan

        while not self.found:

            # Translate the plan in a propositional formula
            planning_formula = self.encoder.encode(self.horizon)

            # Solve the built formula using CDCL solver (Random Heuristic)
            h = RandomHeuristic()
            s = Solver(planning_formula, h, True)

            # planning_formula is satisfied
            if s.run():
                # exit the loop
                self.found = True
                # Create a plan object
                final_plan = Plan(s, encoder)

            # faccio traduzione inversa
            # a un numero corrisponde azione a certo step

            # Increase horizon
            self.horizon += 1

            print(self.encoder.actions[0].name)

        # Must return a plan object
        # when plan is found
        return final_plan
