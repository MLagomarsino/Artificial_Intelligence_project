# encoding: utf-8
import translate.pddl as pddl
import utils
from formula import FormulaMgr
from translate import instantiate
from translate import numeric_axiom_rules
from collections import defaultdict
import numpy as np


class Encoder():

    def __init__(self, task, modifier):

        self.task = task
        # generates axioms (linear (1 action at time -> series)
        # and parallel (+ non conflicting actions))
        self.modifier = modifier

        # grounding (all combinations of params) -> do it for each instant
        (self.boolean_fluents,
         self.actions,
         self.numeric_fluents,
         self.axioms,
         self.numeric_axioms) = self.ground()

        # don't touch
        (self.axioms_by_name,
         self.depends_on,
         self.axioms_by_layer) = self.sort_axioms()

        # attention to concurrent actions (linear: don't need to modify!!)
        self.mutexes = self.computeMutexes()

        # Add formula mgr
        self.formula_mgr = FormulaMgr()

        # Inverse mapping: create a (unique) list to store associations
        self.inverse = [None]  # first element of the list is none
        # Create boolean variables for boolean fluents
        self.boolean_variables = defaultdict(dict)
        # Create propositional variables for actions ids
        self.action_variables = defaultdict(dict)

    def ground(self):
        """
        Ground action schemas:
        This operation leverages optimizations
        implemented in the parser of the
        Temporal Fast-Downward planner
        """

        (relaxed_reachable, bool_fluents, numeric_fluents, bool_actions,
         durative_actions, axioms, numeric_axioms,
         reachable_action_params) = instantiate.explore(self.task)

        # TODO MARTAAAA !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Check consistency of fluents
        boolean_fluents = set()

        for fluent in bool_fluents:
            number_arg = len(fluent.args)
            if number_arg == 2:
                # Check consistency of the fluent
                a1 = fluent.args[0]
                a2 = fluent.args[1]
                if not a1 == a2:
                    boolean_fluents.add(fluent)
            else:
                boolean_fluents.add(fluent)

        # Check consistency of actions
        # Avoid invalid actions such as (stack a a) -> same object
        actions = list()
        for action in bool_actions:
            a_name = action.name[:-1].split(' ')

            if not a_name[-1] == a_name[-2]:
                actions.append(action)

        return boolean_fluents, actions, numeric_fluents, axioms, numeric_axioms

    def sort_axioms(self):
        """
        Returns 3 dictionaries:
        - axioms sorted by name
        - dependencies between axioms
        - axioms sorted by layer
        """

        axioms_by_name = {}
        for nax in self.numeric_axioms:
            axioms_by_name[nax.effect] = nax

        # special dictionary that returns an empty list if the key doesn't exist
        depends_on = defaultdict(list)
        for nax in self.numeric_axioms:
            for part in nax.parts:
                depends_on[nax].append(part)

        axioms_by_layer, _, _, _ = numeric_axiom_rules.handle_axioms(self.numeric_axioms)

        return axioms_by_name, depends_on, axioms_by_layer

    def computeMutexes(self):
        """
        Compute mutually exclusive actions using the conditions
        we saw during lectures
        """

        mutexes = []
        for a1 in self.actions:
            for a2 in self.actions:
                if not a1.name == a2.name:
                    pass

        return mutexes

    def createVariables(self):
        # First step of translation: FOL -> PL (Grounding)

        # associate to each action or fluent an identifier (called counter)
        # store the mappings in a appropriate structure

        # create a dictionary of dictionaries:
        # 1 level = step, 2 level = action or fluent
        # value of the couple of keys (of the two levels) is a number (unique for config)
        # if a is a dictionary: a[0]["pickup a"]

        # unique counter to identify fluents and actions
        counter = 1

        # a dictionary of 2 levels is created:
        # level1 = steps ; level2 = fluents
        for step in range(self.horizon + 1):
            for fluent in self.boolean_fluents:

                # Direct mapping: assign variable and increment the counter to obtain a unique identifier
                self.boolean_variables[step][str(fluent)] = counter
                counter += 1
                # Inverse mapping
                self.inverse.append((str(fluent), step))
                #self.inverse.append(str(fluent) + "@" + str(step))

        # a dictionary of 2 levels is created:
        # level1 = steps ; level2 = actions
        for step in range(self.horizon):
            for a in self.actions:

                # Direct mapping
                self.action_variables[step][a.name] = counter
                counter += 1
                # Inverse mapping
                self.inverse.append((str(a.name), step))
                #self.inverse.append(str(a.name) + "@" + str(step))

    def encodeInitialState(self):
        """
        Encode formula defining initial state
        """

        initial = []

        for fact in self.task.init:
            if utils.isBoolFluent(fact):
                if not fact.predicate == '=':
                    if fact in self.boolean_fluents:
                        # M: fluents specifying the initial state
                        code = self.boolean_variables[0][str(fact)]
                        initial.append(self.formula_mgr.mkVar(code))
            else:
                raise Exception('Initial condition \'{}\': type \'{}\' not recognized'.format(fact, type(fact)))

        # Close-world assumption: if fluent is not asserted
        # in init formula then it must be set to false.

        for variable in self.boolean_variables[0].values():
            v = self.formula_mgr.mkVar(variable)
            if v not in initial:
                negated_v = self.formula_mgr.mkNot(v)
                initial.append(negated_v)

        # Encode initial state as a formula
        initial_state = self.formula_mgr.mkAndArray(initial)

        return initial_state

    def encodeGoalState(self):
        """
        Encode formula defining goal state
        """

        propositional_subgoal = []

        # UGLY HACK: we skip atomic propositions that are added
        # to handle numeric axioms by checking names.
        axiom_names = [axiom.name for axiom in self.task.axioms]

        goal = self.task.goal

        # Check if goal is just a single atom
        if isinstance(goal, pddl.conditions.Atom):
            if goal.predicate not in axiom_names: # ?? axiom name ??
                # MARTA!! If the goal is in my list of variables associated to available fluents
                if goal in self.boolean_fluents:
                    propositional_subgoal.append(self.formula_mgr.mkVar(self.boolean_variables[self.horizon][str(goal)]))  # M

        # Check if goal is a conjunction
        elif isinstance(goal, pddl.conditions.Conjunction):
            for fact in goal.parts:
                # MARTA!! If the goal is in my list of variables associated to available fluents
                if fact in self.boolean_fluents:
                    goal_index = self.boolean_variables[self.horizon][str(fact)]
                    propositional_subgoal.append(self.formula_mgr.mkVar(goal_index))  # M

        else:
            raise Exception(
                'Propositional goal condition \'{}\': type \'{}\' not recognized'.format(goal, type(goal)))

        # Encode goal in a formula
        goal = self.formula_mgr.mkAndArray(propositional_subgoal)

        return goal

    def encodeActions(self):
        """
        Encode action constraints:
        each action variable implies its preconditions
        and effects
        """

        # Create dictionary with key
        actions = []
        action_implication = []

        for step in range(0, self.horizon):

            for action in self.actions:

                action_name = self.formula_mgr.mkVar(self.action_variables[step][action.name])

                # Encode preconditions
                preconditions = list()
                for pre in action.condition:
                    if pre in self.boolean_fluents:
                        preconditions.append(self.formula_mgr.mkVar(self.boolean_variables[step][str(pre)]))  # M

                # AND of all preconditions at step
                allpreconditions = self.formula_mgr.mkAndArray(preconditions)
                # Action implies the AND of all preconditions at step
                imply_prec = self.formula_mgr.mkImply(action_name, allpreconditions)

                # Encode add effects (conditional supported)
                add_effects = list()
                for add in action.add_effects:
                    add = add[1]
                    if add in self.boolean_fluents:
                        add_effects.append(self.formula_mgr.mkVar(self.boolean_variables[step+1][str(add)]))

                # AND of all effects added at the following step
                alladdeffects = self.formula_mgr.mkAndArray(add_effects)
                # Action implies the AND of all effects added at the following step
                imply_addeffects = self.formula_mgr.mkImply(action_name, alladdeffects)

                # Encode delete effects (conditional supported)
                del_effects = list()
                for de in action.del_effects:
                    de = de[1]
                    if de in self.boolean_fluents:
                        del_effects.append(self.formula_mgr.mkNot(self.formula_mgr.mkVar(self.boolean_variables[step+1][str(de)])))

                # AND of all effects deleted at the following step
                alldeleffects = self.formula_mgr.mkAndArray(del_effects)
                # Action implies the AND of all effects deleted at the following step
                imply_deleffects = self.formula_mgr.mkImply(action_name, alldeleffects)

                # AND of imply_prec, imply_addeffects and imply_deleffects
                action_implication.append(self.formula_mgr.mkAndArray([imply_prec, imply_addeffects, imply_deleffects]))

            # AND of all implications of actions
            actions.append(self.formula_mgr.mkAndArray(action_implication))

        # AND of all steps
        return self.formula_mgr.mkAndArray(actions)

    def encodeFrame(self):
        """
        Encode explanatory frame axioms
        """

        all_fluents = []

        actions_deliting = defaultdict(list)
        actions_adding = defaultdict(list)

        # Check fluent can change its value due to an action
        for fluent in self.boolean_fluents:

            swap_pos2neg = 0
            swap_neg2pos = 0

            # Check fluent changes its value, this means that an action is performed
            for action in self.actions:

                # Check fluent is added by an action
                for add_e in action.add_effects:
                    if fluent == add_e[1]:
                        swap_neg2pos = 1
                        # Save action changing value of the fluent from negative to positive
                        actions_adding[fluent].append(action.name)
                        break

                # Check fluent is a precondition of the action
                if fluent in action.condition:

                    # Check fluent is deleted by the action
                    for del_e in action.del_effects:
                        if fluent == del_e[1]:
                            swap_pos2neg = 1
                            # Save action changing value of the fluent from positive to negative
                            actions_deliting[fluent].append(action.name)
                            break

        for step in range(self.horizon):
            frame = list()

            for fluent in self.boolean_fluents:

                pos_performed_actions = list()
                neg_performed_actions = list()

                # Same fluent at two adjacent steps
                f_step = self.formula_mgr.mkVar(self.boolean_variables[step][str(fluent)])
                f_stepplus1 = self.formula_mgr.mkVar(self.boolean_variables[step + 1][str(fluent)])

                if not swap_neg2pos:
                    # If fluent is false at step i is false also at step i+1

                    # Negation of fluent at current step
                    not_f_step = self.formula_mgr.mkNot(f_step)
                    # Negation of fluent at following step
                    not_f_stepplus1 = self.formula_mgr.mkNot(f_stepplus1)

                    frame.append(self.formula_mgr.mkImply(not_f_step, not_f_stepplus1))

                else:
                    # The fluent can be added by at least one action

                    # Negation of fluent at following step
                    not_f_step = self.formula_mgr.mkNot(f_step)

                    # Value changes implies at least one action is performed
                    adjacent_fluents = self.formula_mgr.mkAnd(not_f_step, f_stepplus1)

                    # OR of all actions that change the value of that fluent (at least one)
                    for act in actions_adding[fluent]:
                        pos_performed_actions.append(self.formula_mgr.mkVar(self.action_variables[step][act]))
                    atleastone_action = self.formula_mgr.mkOrArray(pos_performed_actions)

                    frame.append(self.formula_mgr.mkImply(adjacent_fluents, atleastone_action))

                if not swap_pos2neg:
                    # If fluent is true at step i is true also at step i+1
                    frame.append(self.formula_mgr.mkImply(f_step, f_stepplus1))
                else:
                    # The fluent can be delete by at least one action

                    # Negation of fluent at following step
                    not_f_stepplus1 = self.formula_mgr.mkNot(f_stepplus1)

                    # Value changes implies at least one action is performed
                    adjacent_fluents = self.formula_mgr.mkAnd(f_step, not_f_stepplus1)

                    # OR of all actions that change the value of that fluent (at least one)
                    for act in actions_deliting[fluent]:
                        neg_performed_actions.append(self.formula_mgr.mkVar(self.action_variables[step][act]))
                    atleastone_action = self.formula_mgr.mkOrArray(neg_performed_actions)

                    frame.append(self.formula_mgr.mkImply(adjacent_fluents, atleastone_action))

            all_fluents.append(self.formula_mgr.mkAndArray(frame))

        return self.formula_mgr.mkAndArray(all_fluents)

    def encodeExecutionSemantics(self):

        try:
            return self.modifier.do_encode(self.action_variables, self.horizon, self.formula_mgr)
        except:
            return self.modifier.do_encode(self.action_variables, self.horizon, self.formula_mgr)#, self.mutexes)


    def encodeAtLeastOne(self):

        atleastone_forstep = list()
        atleastone = list()

        for step in range(self.horizon):

            for action in self.actions:
                action_code = self.action_variables[step][str(action.name)]
                atleastone_forstep.append(self.formula_mgr.mkVar(action_code))

            # at least one action should be performed at each step -> OR of all variables of the step
            atleastone.append(self.formula_mgr.mkOrArray(atleastone_forstep))

        # return logic AND of all steps
        return self.formula_mgr.mkAndArray(atleastone)

    def encode(self, horizon):
        # type: (object) -> object
        """
        Basic routine for bounded encoding:
        encodes initial, transition, goal conditions
        together with frame and exclusiveness/mutexes axioms

        """
        self.horizon = horizon

        # Create variables
        self.createVariables()

        # Start encoding formula

        formula = defaultdict(list)

        # Formula Manager
        self.formula_mgr = FormulaMgr()

        # Encode initial state axioms

        formula['initial'] = self.encodeInitialState()

        # Encode goal state axioms

        formula['goal'] = self.encodeGoalState()

        # Encode universal axioms

        formula['actions'] = self.encodeActions()

        # Encode explanatory frame axioms

        formula['frame'] = self.encodeFrame()

        # Encode execution semantics (lin/par)

        formula['sem'] = self.encodeExecutionSemantics()

        # Encode at least one axioms

        formula['alo'] = self.encodeAtLeastOne()

        # Put the values of the dictionary in a list
        planning_list = [v for v in formula.values()]

        # Build planning formula
        return self.formula_mgr.mkAndArray(planning_list)

    def dump(self):
        print('Dumping encoding')
        raise Exception('Not implemented yet')