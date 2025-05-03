# symbolic_type.py
# Updated to use getfullargspec for Python 3 compatibility
import inspect
import functools

# the ABSTRACT base class for representing any expression that depends on a symbolic input
# it also tracks the corresponding concrete value for the expression (aka concolic execution)

class SymbolicType(object):
    def __init__(self, name, expr=None):
        self.name = name
        self.expr = expr

    def getConcrValue(self):
        raise NotImplemented()

    @staticmethod
    def wrap(conc, sym):
        raise NotImplemented()

    def isVariable(self):
        return self.expr is None

    def unwrap(self):
        if self.isVariable():
            return (self.getConcrValue(), self)
        else:
            return (self.getConcrValue(), self.expr)

    def getVars(self):
        if self.isVariable():
            return [self.name]
        elif isinstance(self.expr, list):
            return self._getVarsLeaves(self.expr)
        else:
            return []

    def _getVarsLeaves(self, l):
        if isinstance(l, list):
            return functools.reduce(lambda a, x: self._getVarsLeaves(x) + a, l, [])
        elif isinstance(l, SymbolicType):
            return [l.name]
        else:
            return []

    def _do_sexpr(self, args, fun, op, wrap):
        # Unwrap arguments to (concrete, symbolic) pairs
        unwrapped = [(a.unwrap() if isinstance(a, SymbolicType) else (a, a)) for a in args]
        # Use getfullargspec for Python 3
        spec = inspect.getfullargspec(fun).args
        # Map argument names to concrete values
        concrete_args = {name: val for name, (val, _) in zip(spec, unwrapped)}
        concrete = fun(**concrete_args)
        # Build symbolic expression list: [op, *symbolic parts]
        symbolic = [op] + [sym for (_, sym) in unwrapped]
        return wrap(concrete, symbolic)

    def symbolicEq(self, other):
        if not isinstance(other, SymbolicType):
            return False
        if self.isVariable() or other.isVariable():
            return self.name == other.name
        return self._eq_worker(self.expr, other.expr)

    def _eq_worker(self, expr1, expr2):
        if type(expr1) != type(expr2):
            return False
        if isinstance(expr1, list):
            return len(expr1) == len(expr2) and\
                   type(expr1[0]) == type(expr2[0]) and\
                   all(self._eq_worker(x, y) for x, y in zip(expr1[1:], expr2[1:]))
        elif isinstance(expr1, SymbolicType):
            return expr1.name == expr2.name
        else:
            return expr1 == expr2

    def toString(self):
        if self.isVariable():
            return f"{self.name}#{self.getConcrValue()}"
        else:
            return self._toString(self.expr)

    def _toString(self, expr):
        if isinstance(expr, list):
            return "(" + expr[0] + " " + ", ".join(self._toString(a) for a in expr[1:]) + ")"
        elif isinstance(expr, SymbolicType):
            return expr.toString()
        else:
            return str(expr)

class SymbolicObject(SymbolicType):
    def __init__(self, name, expr=None):
        super().__init__(name, expr)

    SI = None  # Set by ExplorationEngine to link control-flow

    def __bool__(self):
        concrete = bool(self.getConcrValue())
        if SymbolicObject.SI is not None:
            SymbolicObject.SI.whichBranch(concrete, self)
        return concrete

    def _do_bin_op(self, other, fun, op, wrap):
        return self._do_sexpr([self, other], fun, op, wrap)

    def __eq__(self, other):
        return self._do_bin_op(other, lambda x, y: x == y, "==", SymbolicObject.wrap)

    def __ne__(self, other):
        return self._do_bin_op(other, lambda x, y: x != y, "!=", SymbolicObject.wrap)

    def __lt__(self, other):
        return self._do_bin_op(other, lambda x, y: x < y, "<", SymbolicObject.wrap)

    def __le__(self, other):
        return self._do_bin_op(other, lambda x, y: x <= y, "<=", SymbolicObject.wrap)

    def __gt__(self, other):
        return self._do_bin_op(other, lambda x, y: x > y, ">", SymbolicObject.wrap)

    def __ge__(self, other):
        return self._do_bin_op(other, lambda x, y: x >= y, ">=", SymbolicObject.wrap)
