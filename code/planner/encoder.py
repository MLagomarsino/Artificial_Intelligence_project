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
        self.modifier = modifier  # genera assiomi (linear (1 azione per volta -> serie) e parallel (+ azioni non in conflitto))

        # grounding (all combinations of params) -> fare per ogni istante
        (self.boolean_fluents,
         self.actions,
         self.numeric_fluents,
         self.axioms,
         self.numeric_axioms) = self.ground()

        # don't touch
        (self.axioms_by_name,
         self.depends_on,
         self.axioms_by_layer) = self.sort_axioms()

        # attention to conflictable actions (per linear non serve modificare!!)
        self.mutexes = self.computeMutexes()

        # Add formula mgr
        self.formula_mgr = FormulaMgr()

        # TODO delete!
        self.horizon = 2
        self.createVariables()

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
        # First step of translation: FOL -> PL

        # associate to each action or fluent an identifier (called counter)
        # store the mappings in a appropriate structure

        # creo un dizionario di diz : 1 livello = step, 2 livello = azione o fluente
        # valore coppia di chiavi (dei due livelli) e' un numero (unico, per configurazione)
        # se a e' dizionario
        # a[0]["pickup a"]

        # unique counter to identify fluents and actions
        counter = 1
        # Inverse mapping: create a (unique) list to store associations
        self.inverse = [None]  # first element of the list is none

        # Create boolean variables for boolean fluents
        self.boolean_variables = defaultdict(dict)
        # a dictionary of 2 levels is created:
        #   level1 = steps ; level2 = fluents
        for step in range(self.horizon + 1):
            for fluent in self.boolean_fluents:
                # Direct mapping: assign variable and increment the counter to obtain a unique identifier
                self.boolean_variables[step][str(fluent)] = counter
                counter += 1
                # Inverse mapping: append couple (fluent, step)
                self.inverse.append((str(fluent), step))

        # Create propositional variables for actions ids
        self.action_variables = defaultdict(dict)
        # a dictionary of 2 levels is created:
        #   level1 = steps ; level2 = actions
        for step in range(self.horizon):
            for a in self.actions:
                # Direct mapping
                self.action_variables[step][str(a)] = counter
                counter += 1
                # Inverse mapping: append couple (action, step)
                self.inverse.append((str(a), step))

    def encodeInitialState(self):
        """
        Encode formula defining initial state
        """

        initial = []

        for fact in self.task.init:

            if utils.isBoolFluent(fact):
                if not fact.predicate == '=':
                    if fact in self.boolean_fluents:
                        pass

            else:
                raise Exception('Initial condition \'{}\': type \'{}\' not recognized'.format(fact, type(fact)))

        # Close-world assumption: if fluent is not asserted
        # in init formula then it must be set to false.

        for variable in self.boolean_variables.values():
            if not variable in initial:
                pass

        return initial

    def encodeGoalState(self):
        """
        Encode formula defining goal state
        """

        def encodePropositionalGoals(goal=None):

            propositional_subgoal = []

            # UGLY HACK: we skip atomic propositions that are added
            # to handle numeric axioms by checking names.
            axiom_names = [axiom.name for axiom in self.task.axioms]

            if goal is None:
                goal = self.task.goal

            # Check if goal is just a single atom
            if isinstance(goal, pddl.conditions.Atom):
                if not goal.predicate in axiom_names:
                    pass

            # Check if goal is a conjunction
            elif isinstance(goal, pddl.conditions.Conjunction):
                for fact in goal.parts:
                    pass

            else:
                raise Exception(
                    'Propositional goal condition \'{}\': type \'{}\' not recognized'.format(goal, type(goal)))

            return propositional_subgoal

        propositional_subgoal = encodePropositionalGoals()
        goal = And(propositional_subgoal)

        return goal

    def encodeActions(self):
        """
        Encode action constraints:
        each action variable implies its preconditions
        and effects
        """

        actions = []

        for step in range(self.horizon):
            for action in self.actions:

                # Encode preconditions
                for pre in action.condition:
                    pass

                # Encode add effects (conditional supported)
                for add in action.add_effects:
                    pass

                # Encode delete effects (conditional supported)
                for de in action.del_effects:
                    pass

        return actions

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
        """
        Basic routine for bounded encoding:
        encodes initial, transition,goal conditions
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


class EncoderSAT(Encoder):

    def encode(self, horizon):
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

        return formula
