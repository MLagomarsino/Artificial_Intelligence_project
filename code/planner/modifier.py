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

        # TODO : implementazione 1 azione per step EXOR
        for step in range(bound):

            for performed_action in variables:

                performed_action_name = formula_mgr.mkVar(variables)

                action_name = list()

                for action in variables:
                    if not action == performed_action:
                        action_name.append(formula_mgr.mkVar(variables[step][action.name]))

                all_actions = formula_mgr.mkNot(formula_mgr.mkAndArray(action_name))

                exor_actions.append(formula_mgr.mkAnd(performed_action_name, all_actions))



        return formula_mgr.mkAndArray(exor_actions)
