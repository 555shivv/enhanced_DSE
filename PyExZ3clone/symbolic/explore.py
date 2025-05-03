from collections import deque
import logging
import os

from .z3_wrap import Z3Wrapper
from .path_to_constraint import PathToConstraint
from .invocation import FunctionInvocation
from .symbolic_types import symbolic_type, SymbolicType
import random

log = logging.getLogger("se.conc")

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
            constraint.inputs=self._getInputs()
        

    def explore(self, max_iterations=0):
        self._oneExecution()

        iterations = 1
        if max_iterations != 0 and iterations >= max_iterations:
            log.debug("Maximum number of iterations reached, terminating")
            return self.execution_return_values

        while not self._isExplorationComplete():
            selected = self.constraints_to_solve.popleft()

            if selected.processed:
                continue
            selected.processed = True  # ✅ Mark it processed here

            self._setInputs(selected.inputs)

            log.info("Selected constraint %s" % selected)
            asserts, query = selected.getAssertsAndQuery()

            print("[*] Solving constraints:")
            for a in asserts:
                print("  -", a)
            print("  Query:", query)

            model = self.solver.findCounterexample(asserts, query)
            if model is None or all(self._getConcrValue(self.symbolic_inputs[k]) == model[k] for k in model):
                 log.debug("Model did not produce new inputs. Skipping.")
                 continue

            if model is None:
                print("[-] No model found.")
                continue
            else:
                print("[+] Found model:")
                for name in model.keys():
                    print(f"    {name} = {model[name]}")
                    self._updateSymbolicParameter(name, model[name])

            self._oneExecution(selected)
            iterations += 1
            self.num_processed_constraints += 1

            if max_iterations != 0 and iterations >= max_iterations:
                log.info("Maximum number of iterations reached, terminating")
                break

        total, covered = self.path.getConditionCoverage()
        coverage = (covered / total * 100) if total > 0 else 100.0
        print(f"Condition Coverage using DSE: {covered}/{total} ({coverage:.2f}%)")

        return self.generated_inputs, self.execution_return_values, self.path

    def _updateSymbolicParameter(self, name, val):
        self.symbolic_inputs[name] = self.invocation.createArgumentValue(name, val)

    def _getInputs(self):
        return self.symbolic_inputs.copy()

    def _setInputs(self, d):
        self.symbolic_inputs = d

    def _isExplorationComplete(self):
        num_constr = len(self.constraints_to_solve)
        if num_constr == 0:
            log.info("Exploration complete")
            return True
        else:
            log.info("%d constraints yet to solve (total: %d, already solved: %d)" % (
                num_constr, self.num_processed_constraints + num_constr, self.num_processed_constraints))
            return False

    def _getConcrValue(self, v):
        if isinstance(v, SymbolicType):
            return v.getConcrValue()
        else:
            return v

    def _recordInputs(self):
        args = self.symbolic_inputs
        print("  [*] Input types:")
        for k, v in args.items():
            print(f"    {k}: {v} ({type(v)})")

        inputs = [(k, self._getConcrValue(args[k])) for k in args]
        self.generated_inputs.append(inputs)
        print(inputs)
    
    def _oneExecution(self, expected_path=None):
        self._recordInputs()
        self.path.reset(expected_path)
        ret = self.invocation.callFunction(self.symbolic_inputs)
        print(ret)
        self.execution_return_values.append(ret)
