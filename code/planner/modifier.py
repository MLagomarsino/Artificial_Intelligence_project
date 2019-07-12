from encoder import Encoder
from formula import FormulaMgr

class Modifier():

    def do_encode(self):
        pass

class LinearModifier(Modifier):

    def do_encode(self, variables, bound):
        # M: add mutex
        exor_actions = []
        formula_mgr = FormulaMgr()

        # One action at each step
        for step in range(bound):

            for performed_action in variables[step]:

                # Performed action
                performed_action_code = formula_mgr.mkVar(variables[step][performed_action])

                not_performed_action_code = list()
                all_actions = list()

                for action in variables[step]:
                    # Not performed actions
                    if not action == performed_action:
                        action_code = formula_mgr.mkVar(variables[step][action])
                        not_performed_action_code.append(formula_mgr.mkNot(action_code))

                # If I perform performed_action, I don't perform all the others
                not_performed_action_code.insert(0, performed_action_code)
                all_actions.append(formula_mgr.mkAndArray(not_performed_action_code))

            # EXOR for each step
            exor_actions.append(formula_mgr.mkOrArray(all_actions))

        return formula_mgr.mkAndArray(exor_actions)
