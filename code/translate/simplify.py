# -*- coding: utf-8 -*-

from collections import defaultdict
from itertools import count
import sys

DEBUG = True


# TODO:
# This is all quite hackish and would be easier if the translator were
# restructured so that more information is immediately available for
# the propositions, and if propositions had more structure. Directly
# working with int pairs is awkward.


class DomainTransitionGraph(object):
    def __init__(self, init, size):
        self.init = init
        self.size = size
        self.arcs = defaultdict(set)

    def add_arc(self, u, v):
        self.arcs[u].add(v)

    def reachable(self):
        queue = [self.init]
        reachable = set(queue)
        while queue:
            node = queue.pop()
            new_neighbors = self.arcs.get(node, set()) - reachable
            reachable |= new_neighbors
            queue.extend(new_neighbors)
        return reachable

    def dump(self):
        print "SIZE", self.size
        print "INIT", self.init
        print "ARCS:"
        for source, destinations in sorted(self.arcs.items()):
            for destination in sorted(destinations):
                print "  %d => %d" % (source, destination)


def build_dtgs(task):
    init_vals = task.init.values
    sizes = task.variables.ranges
    dtgs = [DomainTransitionGraph(init, size)
            for (init, size) in zip(init_vals, sizes)]

    def add_arc(var_no, pre_spec, post):
        if pre_spec == -1:
            pre_values = set(range(sizes[var_no])).difference([post])
        else:
            pre_values = [pre_spec]
        for pre in pre_values:
            dtgs[var_no].add_arc(pre, post)

    for op in task.operators:
        for var_no, pre_spec, post, cond in op.pre_post:
            add_arc(var_no, pre_spec, post)
    for axiom in task.axioms:
        var_no, val = axiom.effect
        add_arc(var_no, -1, val)

    return dtgs


always_false = object()
always_true = object()


class Impossible(Exception):
    pass


class DoesNothing(Exception):
    pass


class VarValueRenaming(object):
    def __init__(self):
        self.new_var_nos = []  # indexed by old var_no
        self.new_values = []  # indexed by old var_no and old value
        self.new_sizes = []  # indexed by new var_no
        self.new_var_count = 0
        self.num_removed_values = 0

    def register_variable(self, old_domain_size, init_value, new_domain):
        assert 1 <= len(new_domain) <= old_domain_size
        assert init_value in new_domain
        if len(new_domain) == 1:
            # Remove this variable completely.
            new_values_for_var = [always_false] * old_domain_size
            new_values_for_var[init_value] = always_true
            self.new_var_nos.append(None)
            self.new_values.append(new_values_for_var)
            self.num_removed_values += old_domain_size
        else:
            new_value_counter = count()
            new_values_for_var = []
            for value in range(old_domain_size):
                if value in new_domain:
                    new_values_for_var.append(new_value_counter.next())
                else:
                    self.num_removed_values += 1
                    new_values_for_var.append(always_false)
            new_size = new_value_counter.next()
            assert new_size == len(new_domain)

            self.new_var_nos.append(self.new_var_count)
            self.new_values.append(new_values_for_var)
            self.new_sizes.append(new_size)
            self.new_var_count += 1

    def apply_to_task(self, task):
        self.apply_to_variables(task.variables)
        self.apply_to_init(task.init)
        self.apply_to_goals(task.goal.pairs)
        self.apply_to_operators(task.operators)
        self.apply_to_axioms(task.axioms)

    def apply_to_variables(self, variables):
        variables.ranges = self.new_sizes
        new_axiom_layers = [None] * self.new_var_count
        for old_no, new_no in enumerate(self.new_var_nos):
            if new_no is not None:
                new_axiom_layers[new_no] = variables.axiom_layers[old_no]
        assert None not in new_axiom_layers
        variables.axiom_layers = new_axiom_layers

    def apply_to_init(self, init):
        init_pairs = list(enumerate(init.values))
        try:
            self.translate_pairs_in_place(init_pairs)
        except Impossible:
            assert False, "Initial state impossible? Inconceivable!"
        new_values = [None] * self.new_var_count
        for new_var_no, new_value in init_pairs:
            new_values[new_var_no] = new_value
        assert None not in new_values
        init.values = new_values

    def apply_to_goals(self, goals):
        # This may propagate Impossible up.
        self.translate_pairs_in_place(goals)

    def apply_to_operators(self, operators):
        new_operators = []
        for op in operators:
            try:
                self.apply_to_operator(op)
                new_operators.append(op)
            except (Impossible, DoesNothing):
                if DEBUG:
                    print "Removed operator: %s" % op.name
        operators[:] = new_operators

    def apply_to_axioms(self, axioms):
        print axioms
        new_axioms = []
        for axiom in axioms:
            try:
                self.apply_to_axiom(axiom)
                new_axioms.append(axiom)
            except (Impossible, DoesNothing):
                if DEBUG:
                    print "Removed axiom:"
                    axiom.dump()
        axioms[:] = new_axioms

    def apply_to_operator(self, op):
        # The prevail translation may generate an Impossible exception,
        # which is propagated up.
        self.translate_pairs_in_place(op.prevail)
        new_pre_post = []
        for entry in op.pre_post:
            try:
                new_pre_post.append(self.translate_pre_post(entry))
                # This may raise Impossible if "pre" is always false.
                # This is then propagated up.
            except DoesNothing:
                # Conditional effect that is impossible to trigger, or
                # effect that sets an always true value. Swallow this.
                pass
        op.pre_post = new_pre_post
        if not new_pre_post:
            raise DoesNothing

    def apply_to_axiom(self, axiom):
        # The following line may generate an Impossible exception,
        # which is propagated up.
        self.translate_pairs_in_place(axiom.condition)
        new_var, new_value = self.translate_pair(axiom.effect)
        # If the new_value is always false, then the condition must
        # have been impossible.
        assert not new_value is always_false
        if new_value is always_true:
            raise DoesNothing
        axiom.effect = new_var, new_value

    def translate_pre_post(self, (var_no, pre, post, cond)):
        new_var_no, new_post = self.translate_pair((var_no, post))
        if pre == -1:
            new_pre = -1
        else:
            _, new_pre = self.translate_pair((var_no, pre))
        if new_pre is always_false:
            raise Impossible
        try:
            self.translate_pairs_in_place(cond)
        except Impossible:
            raise DoesNothing
        assert new_post is not always_false
        if new_pre is always_true:
            assert new_post is always_true
            raise DoesNothing
        elif new_post is always_true:
            assert new_pre == -1
            raise DoesNothing
        return new_var_no, new_pre, new_post, cond

    def translate_pair(self, (var_no, value)):
        new_var_no = self.new_var_nos[var_no]
        new_value = self.new_values[var_no][value]
        return new_var_no, new_value

    def translate_pairs_in_place(self, pairs):
        new_pairs = []
        for pair in pairs:
            new_var_no, new_value = self.translate_pair(pair)
            if new_value is always_false:
                raise Impossible
            elif new_value is not always_true:
                assert new_var_no is not None
                new_pairs.append((new_var_no, new_value))
        pairs[:] = new_pairs

    def apply_to_translation_key(self, translation_key):
        new_key = [[None] * size for size in self.new_sizes]
        for var_no, value_names in enumerate(translation_key):
            for value, value_name in enumerate(value_names):
                new_var_no, new_value = self.translate_pair((var_no, value))
                if new_value is always_true:
                    if DEBUG:
                        print "Removed true proposition: %s" % value_name
                elif new_value is always_false:
                    if DEBUG:
                        print "Removed false proposition: %s" % value_name
                else:
                    new_key[new_var_no][new_value] = value_name
        assert all((None not in value_names) for value_names in new_key)
        translation_key[:] = new_key

    def apply_to_mutex_key(self, mutex_key):
        new_key = []
        for group in mutex_key:
            new_group = []
            for var, val, name in group:
                new_var_no, new_value = self.translate_pair((var, val))
                if (new_value is not always_true and
                        new_value is not always_false):
                    new_group.append((new_var_no, new_value, name))
            if len(new_group) > 0:
                new_key.append(new_group)
        mutex_key[:] = new_key


def build_renaming(dtgs):
    renaming = VarValueRenaming()
    for dtg in dtgs:
        renaming.register_variable(dtg.size, dtg.init, dtg.reachable())
    return renaming


def dump_translation_key(translation_key):
    for var_no, values in enumerate(translation_key):
        print "var %d:" % var_no
        for value_no, value in enumerate(values):
            print "%2d: %s" % (value_no, value)


def filter_unreachable_propositions(sas_task, mutex_key, translation_key):
    print "**sas_task"
    sas_task.output(sys.stdout)
    print "Detecting unreachable propositions...",
    sys.stdout.flush()
    if DEBUG:
        print

    # This procedure is a bit of an afterthought, and doesn't fit the
    # overall architecture of the translator too well. We filter away
    # unreachable propositions here, and then prune away variables
    # with only one value left.
    # 
    # Examples of things that are filtered away:
    # - Constant propositions that are not detected in instantiate.py
    #   because it only reasons at the predicate level, and some
    #   predicates such as "at" in Depot is constant for some objects
    #   (hoists), but not others (trucks).
    #   Example: "at(hoist1, distributor0)" and the associated
    #            variable in depots-01.
    # - "none of those" values that are unreachable.
    #   Example: at(truck1, ?x) = <none of those> in depots-01.
    # - Certain values that are relaxed reachable but detected as
    #   unreachable after SAS instantiation because the only operators
    #   that set them have inconsistent preconditions.
    #   Example: on(crate0, crate0) in depots-01.

    # dump_translation_key(translation_key)
    dtgs = build_dtgs(sas_task)
    renaming = build_renaming(dtgs)
    # apply_to_task may propagate up Impossible if the goal is simplified
    # to False.
    renaming.apply_to_task(sas_task)
    renaming.apply_to_translation_key(translation_key)
    renaming.apply_to_mutex_key(mutex_key)
    print "%d propositions removed." % renaming.num_removed_values


def constrain_end_effect_conditions(sas_task):
    pre_by_operator_and_var = dict();
    start_eff_by_operator_and_var = dict();
    var_to_influencing_ops = dict();
    interesting = dict();  ## var->list<op> operators for which the effect
    ## condition could possibly be constrained
    for op in sas_task.temp_operators:
        start_prevail = op.prevail[0]
        for var, val in start_prevail:
            pre_by_operator_and_var[(op, var)] = val
        pre_post = op.pre_post
        start_eff = dict()
        for var, pre, post, cond in pre_post[0]:
            pre_by_operator_and_var[(op, var)] = pre
            if cond == [[], [], []]:
                start_eff[var] = post
                start_eff_by_operator_and_var[(op, var)] = post
            var_to_influencing_ops.setdefault(var, set()).add(op)
        for var, pre, post, cond in pre_post[1]:
            var_to_influencing_ops.setdefault(var, set()).add(op)
            if pre == -1:
                start_val = start_eff.get(var, None)
                if start_val is not None:
                    interesting.setdefault(var, []).append(op)

    variables_to_change = dict()
    for var in interesting.iterkeys():
        influencing = var_to_influencing_ops[var]
        var_is_candidate = True
        for op1 in influencing:
            if not var_is_candidate:
                break
            for op2 in influencing:  ## check that op2 cannot be started while
                ## op1 is running
                cond2 = pre_by_operator_and_var.get((op2, var), None)
                start_eff1 = start_eff_by_operator_and_var.get((op1, var), None)
                if None in (cond2, start_eff1) or start_eff1 == cond2:
                    var_is_candidate = False
                    break
        if var_is_candidate:
            for op in interesting[var]:
                variables_to_change.setdefault(op, set()).add(var)

    nr_changed = 0
    for op, vars in variables_to_change.iteritems():
        for index, (var, pre, post, cond) in enumerate(op.pre_post[1]):
            if var in vars and pre == -1:
                new_pre = start_eff_by_operator_and_var[(op, var)]
                op.pre_post[1][index] = (var, new_pre, post, cond)
                nr_changed += 1

    print "constrained %s conditions" % nr_changed
