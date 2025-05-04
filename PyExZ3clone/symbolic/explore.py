from collections import deque
import logging
import os

from .z3_wrap import Z3Wrapper
from .path_to_constraint import PathToConstraint
from .invocation import FunctionInvocation
from .symbolic_types import symbolic_type, SymbolicType
import random

# 🔧 Rich import
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()
log = logging.getLogger("se.conc")

# ... [imports and class init stay the same]

class ExplorationEngine:
    def __init__(self, funcinv, solver="z3"):
        self.invocation = funcinv
        self.symbolic_inputs = {}
        for n in funcinv.getNames():
            self.symbolic_inputs[n] = funcinv.createArgumentValue(n)

        self.constraints_to_solve = deque([])
        self.num_processed_constraints = 0

        self.path = PathToConstraint(lambda c: self.addConstraint(c))
        symbolic_type.SymbolicObject.SI = self.path

        if solver == "z3":
            self.solver = Z3Wrapper()
        elif solver == "cvc":
            from .cvc_wrap import CVCWrapper
            self.solver = CVCWrapper()
        else:
            raise Exception("Unknown solver %s" % solver)

        self.generated_inputs = []
        self.execution_return_values = []

    def addConstraint(self, constraint):
        if constraint not in self.constraints_to_solve:
            self.constraints_to_solve.append(constraint)
            constraint.inputs = self._getInputs()

    def explore(self, max_iterations=0):
        print(" Starting symbolic exploration...\n")
        self._oneExecution()

        iterations = 1
        if max_iterations != 0 and iterations >= max_iterations:
            return self.execution_return_values

        while not self._isExplorationComplete():
            selected = self.constraints_to_solve.popleft()
            if selected.processed:
                continue
            selected.processed = True

            self._setInputs(selected.inputs)
            asserts, query = selected.getAssertsAndQuery()

            model = self.solver.findCounterexample(asserts, query)
            if model is None or all(self._getConcrValue(self.symbolic_inputs[k]) == model[k] for k in model):
                continue

            for name in model.keys():
                self._updateSymbolicParameter(name, model[name])

            self._oneExecution(selected)
            iterations += 1
            self.num_processed_constraints += 1

            if max_iterations != 0 and iterations >= max_iterations:
                break

        # Print Summary
        self._printSummary()
        return self.generated_inputs, self.execution_return_values, self.path

    def _updateSymbolicParameter(self, name, val):
        self.symbolic_inputs[name] = self.invocation.createArgumentValue(name, val)

    def _getInputs(self):
        return self.symbolic_inputs.copy()

    def _setInputs(self, d):
        self.symbolic_inputs = d

    def _isExplorationComplete(self):
        return len(self.constraints_to_solve) == 0

    def _getConcrValue(self, v):
        return v.getConcrValue() if isinstance(v, SymbolicType) else v

    def _recordInputs(self):
        inputs = [(k, self._getConcrValue(v)) for k, v in self.symbolic_inputs.items()]
        self.generated_inputs.append(inputs)

    def _oneExecution(self, expected_path=None):
        self._recordInputs()
        self.path.reset(expected_path)
        ret = self.invocation.callFunction(self.symbolic_inputs)
        self.execution_return_values.append(ret)

    def _printSummary(self):
        print("\n" + "="*70)
        print(" Summary of Symbolic Exploration")
        print("="*70)
        for idx, (inputs, ret) in enumerate(zip(self.generated_inputs, self.execution_return_values), 1):
            print(f"\n🔹 Test Case {idx}")
            print("   Inputs:")
            for name, val in inputs:
                print(f"    {name} = {val}")
            print(f"   Return: {ret}")
        
        total, covered = self.path.getConditionCoverage()
        coverage = (covered / total * 100) if total > 0 else 100.0
        print("\n╭─  Condition Coverage using DSE ─╮")
        print(f"│ {covered} / {total} => {coverage:.2f}% coverage         │")
        print("╰───────────────────────────────────╯")
