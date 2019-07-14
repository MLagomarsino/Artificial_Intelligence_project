from collections import defaultdict
import collections
import operator
import utils
import subprocess
import sys
from cdcl_solver.cdcl import Solver

class Plan():
    def __init__(self, model, encoder):
        self.plan = self.extractPlan(model, encoder)
        self.cost = encoder.horizon

    def extractPlan(self, model, encoder):
        """
        Extract linear plan from model of the formula
        """
        plan = []
        #plan = defaultdict(list)

        # Remove negative elements from the list
        model = [item for item in model if item >= 0]
        # Sort the list in ascending order
        model.sort()

        # Extract plan for model
        for lit in model:

            # Check number corresponds to an action (not to a fluent)
            for action in encoder.action_variables:

                if lit in encoder.action_variables[action].values():
                    # Inverse translation: from number to action
                    variable = encoder.inverse[lit]
                    # Add action in the list of plan actions
                    plan.append([variable[1], variable[0]])
                    #plan[variable[0]].append(variable[1])

        #plan_ordered = collections.OrderedDict(sorted(plan.items(), key=operator.itemgetter(1)))

        #return plan_ordered

        return plan

    def do_print(self):

        print("Actions to perform for reaching the goal:")

        for action in self.plan:

            print(action[1] + " @ " + str(action[0]))

        print(" ")


    def validate(self, val, domain, problem):
        from tempfile import NamedTemporaryFile

        print('Validating plan...')

        plan_to_str = ""
        for step in self.plan:
            plan_to_str += str(step[0]) + ":" + str(step[1]) + "\n"
        #"'\n'.join('{}: {}'.format(key, val) for key, val in self.plan.items())

        with NamedTemporaryFile(mode='w+') as temp:

            temp.write(plan_to_str)
            temp.seek(0)

            try:
                output = subprocess.check_output([val, domain, problem, temp.name])

            except subprocess.CalledProcessError as e:

                print('Unknown error, exiting now...')
                sys.exit()

        temp.close()

        if 'Plan valid' in output:
            return plan_to_str
        else:
            return None

    def pprint(self, dest):
        print('Printing plan to {}'.format(dest))
