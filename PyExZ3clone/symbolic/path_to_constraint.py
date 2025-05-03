# Copyright: see copyright.txt

import logging

from .predicate import Predicate
from .constraint import Constraint

log = logging.getLogger("se.pathconstraint")


class PathToConstraint:
    def __init__(self, add):
        self.constraints = {}
        self.add = add
        self.root_constraint = Constraint(None, None)
        self.current_constraint = self.root_constraint
        self.expected_path = None

    def reset(self, expected):
        self.current_constraint = self.root_constraint
        if expected is None:
            self.expected_path = None
        else:
            self.expected_path = []
            tmp = expected
            while tmp.predicate is not None:
                self.expected_path.append(tmp.predicate)
                tmp = tmp.parent

    def whichBranch(self, branch, symobj):
        p_true = Predicate(symobj, True)
        p_false = Predicate(symobj, False)
        taken_pred = p_true if branch else p_false
        taken_node = self.current_constraint.findChild(taken_pred)
        if taken_node is None:
            taken_node = self.current_constraint.addChild(taken_pred)
        log.debug("Stepping into: %s", taken_node)

        # Locate (or create) the *opposite*-branch node
        opp_pred = p_false if branch else p_true
        opp_node = self.current_constraint.findChild(opp_pred)
        if opp_node is None:
            opp_node = self.current_constraint.addChild(opp_pred)
        # Enqueue the opposite side for later, if not already done
        if not opp_node.processed:
            log.debug("Queuing opposite branch for later: %s", opp_node)
            self.add(opp_node)

        # Mark *only* the taken path as done; leave opp_node.processed False
        taken_node.processed = True

        # Advance down the taken path
        self.current_constraint = taken_node

    def toDot(self):
        # print the thing into DOT format
        header = "digraph {\n"
        footer = "\n}\n"
        return header + self._toDot(self.root_constraint) + footer

    def _toDot(self, c):
        if c.parent is None:
            label = "root"
        else:
            label = c.predicate.symtype.toString()
            if not c.predicate.result:
                label = "Not(" + label + ")"
        node = "C" + str(c.id) + " [ label=\"" + label + "\" ];\n"
        edges = ["C" + str(c.id) + " -> " + "C" + str(child.id) + ";\n" for child in c.children]
        return node + "".join(edges) + "".join([self._toDot(child) for child in c.children])

    def getConditionCoverage(self):
        total_conditions = 0
        covered_conditions = 0
        visited = set()

        def dfs(constraint):
            nonlocal total_conditions, covered_conditions
            for child in constraint.children:
                pred = child.predicate
                key = (pred.symtype.toString(), pred.result)

                if key not in visited:
                    total_conditions += 1
                    if child.processed:
                        covered_conditions += 1
                    visited.add(key)

                dfs(child)

        dfs(self.root_constraint)
        return total_conditions, covered_conditions
