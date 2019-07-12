import utils
import subprocess
from CDCL_solver.cdcl import Solver

class Plan():
    def __init__(self, model, encoder):
        self.plan = self.extractPlan(model, encoder)

    def extractPlan(self, model, encoder):
        """
        Extract linear plan from model of the formula
        """
        plan = []

        # Extract plan for model
        for lit in model:

            # Inverse translation: from number to action
            variable = str(encoder.inverse[lit])

            # Check number corresponds to an action (not to a fluent)
            for action in encoder.action_variables:

                temp = encoder.action_variables[action].values()
                if lit in encoder.action_variables[action].values():
                    # Add action in the list of plan actions
                    plan.append(str(encoder.inverse[lit]))

        return plan

    def do_print(self):

        print("Actions to perform for reaching the goal:")

        for action in self.plan:
            print(" " + action)

        print(" ")


    def validate(self, val, domain, problem):
        from tempfile import NamedTemporaryFile

        print('Validating plan...')

        plan_to_str = '\n'.join('{}: {}'.format(key, val) for key, val in self.plan.items())

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
