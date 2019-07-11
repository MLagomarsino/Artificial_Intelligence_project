# encoding: utf-8
import translate.pddl as pddl
import utils
from formula import FormulaMgr, Node
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

        (relaxed_reachable, boolean_fluents, numeric_fluents, actions,
         durative_actions, axioms, numeric_axioms,
         reachable_action_params) = instantiate.explore(self.task)

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
                # Inverse mapping: append couple (fluent, step)
                self.inverse.append((str(fluent), step))

        # a dictionary of 2 levels is created:
        # level1 = steps ; level2 = actions
        for step in range(self.horizon):
            for a in self.actions:
                # Direct mapping
                self.action_variables[step][a.name] = counter ### MARTA : a.name invece di str(a)
                counter += 1
                # Inverse mapping: append couple (action, step)
                self.inverse.append((a.name, step))


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
            if variable not in initial:
                initial.append(self.formula_mgr.mkNot(self.formula_mgr.mkVar(variable)))

        ff = self.formula_mgr.mkVar(initial.pop(0))

        for code in initial:
            # put all sub-goals in AND
            sub_goal = self.formula_mgr.mkVar(code)
            ff = self.formula_mgr.mkAnd(ff, sub_goal)

        return ff

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
                    propositional_subgoal.append(self.boolean_variables[self.horizon][str(goal)])  # M

        # Check if goal is a conjunction
        elif isinstance(goal, pddl.conditions.Conjunction):
            for fact in goal.parts:
                # MARTA!! If the goal is in my list of variables associated to available fluents
                if fact in self.boolean_fluents:
                    propositional_subgoal.append(self.boolean_variables[self.horizon][str(fact)])  # M

                #propositional_subgoal.append(fact)

        else:
            raise Exception(
                'Propositional goal condition \'{}\': type \'{}\' not recognized'.format(goal, type(goal)))

        # Encode goal in a formula     ???????????
        mgr = FormulaMgr()

        # Check if goal is just a single atom -> it's enough

        # Check if goal is a conjunction
        goal = self.formula_mgr.mkVar(propositional_subgoal.pop(0))

        for code in propositional_subgoal:
            # put all sub-goals in AND
            sub_goal = self.formula_mgr.mkVar(code)
            goal = self.formula_mgr.mkAnd(goal, sub_goal)

        return goal

    def f(self, list):
        if len(list)==1 return list[0]
        l1 #prima metà list
        l2 # seconda metà list
        r1 = f(l1)
        r2 = f(l2)
        return mkand(r1,r2)

    def encodeActions(self):
        """
        Encode action constraints:
        each action variable implies its preconditions
        and effects
        """
        mgr = FormulaMgr()
        # Create dictionary with key
        actions = []


        for step in range(0, self.horizon):

            for action in self.actions:

                action_name = self.action_variables[step][action.name]

                # Encode preconditions
                preconditions = list()
                for pre in action.condition:
                    if pre in self.boolean_fluents:
                        preconditions.append(self.boolean_variables[step][str(pre)])  # M


                # Encode add effects (conditional supported)
                add_effects = list()
                for add in action.add_effects:
                    add = add[1]
                    if add in self.boolean_fluents:
                        add_effects.append(self.boolean_variables[step+1][str(add)])

                # Encode delete effects (conditional supported)
                del_effects = list()
                for de in action.del_effects:
                    de = de[1]
                    if de in self.boolean_fluents:
                        del_effects.append(self.boolean_variables[step+1][str(de)])

                a = impl(action, and(preconditions))
                b = impl(action, and(add))
                c = impl(action, and(not(del))
                actions.append(and(a,b,c))

        return and(actions)

    def encodeFrame(self):
        """
        Encode explanatory frame axioms
        """
        frame = []

        for step in range(self.horizon):
            # Encode frame axioms for boolean fluents
            for fluent in self.boolean_fluents:
                pass

        return frame

    def encodeExecutionSemantics(self):

        try:
            return self.modifier.do_encode(self.action_variables, self.horizon)
        except:
            return self.modifier.do_encode(self.action_variables, self.mutexes, self.horizon)

    def encodeAtLeastOne(self):

        atleastone = []

        for step in range(self.horizon):
            pass

        return atleastone

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

        # mettere tutto in AND (devono essere tutte vere)
        # chiamo formula manager dentro formula
        # M: ciclo su tutta lista formula
        # mkAnd

        return formula

    def dump(self):
        print('Dumping encoding')
        raise Exception('Not implemented yet')