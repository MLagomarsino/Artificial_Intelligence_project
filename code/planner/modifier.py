from itertools import combinations


class Modifier():

    def do_encode(self):
        pass


class LinearModifier(Modifier):

    def do_encode(self, variables, bound, formula_mgr):

        # Mutual exclusion
        one_action = list()

        # One action at each step
        for step in range(bound):

            # At most one performed action
            negated_couple = list()
            # Pairs of actions
            v = variables[step]
            for action1, action2 in combinations(v.values(), 2):
                # AND between pair of actions
                action_couple = formula_mgr.mkVarArray([action1, action2])
                AND_couple = formula_mgr.mkAndArray(action_couple)
                # Negation
                negated_couple.append(formula_mgr.mkNot(AND_couple))

            one_action.append(formula_mgr.mkAndArray(negated_couple))

        return formula_mgr.mkAndArray(one_action)
