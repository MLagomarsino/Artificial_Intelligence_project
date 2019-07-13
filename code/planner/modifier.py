from itertools import combinations

class Modifier():

    def do_encode(self):
        pass

class LinearModifier(Modifier):

    def do_encode(self, variables, bound, formula_mgr):

        # Mutual exclusion
        one_action = list()
        #exor_actions = []

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

            # At least one performed (OR of all actions)
            at_least = list()
            at_least.append(formula_mgr.mkOrArray(formula_mgr.mkVarArray(v.values())))

            one_action.append(formula_mgr.mkAndArray(at_least + negated_couple))

            """
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
            """
        return formula_mgr.mkAndArray(one_action)
