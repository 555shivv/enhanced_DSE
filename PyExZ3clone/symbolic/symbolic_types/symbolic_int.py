# symbolic_int.py

from .symbolic_type import SymbolicObject

class SymbolicInteger(SymbolicObject, int):
    # since we are inheriting from int, we need to use __new__
    def __new__(cls, name, v, expr=None):
        return int.__new__(cls, v)

    def __init__(self, name, v, expr=None):
        super().__init__(name, expr)
        self.val = v

    def getConcrValue(self):
        return self.val

    @staticmethod
    def wrap(conc, sym):
        return SymbolicInteger("se", conc, sym)

    def __hash__(self):
        return hash(self.val)

    def __bool__(self):
        # Delegate to SymbolicObject.__bool__, which invokes whichBranch()
        return super().__bool__()  # calls SymbolicObject.__bool__

    def _op_worker(self, args, fun, op):
        return self._do_sexpr(args, fun, op, SymbolicInteger.wrap)


# Hook up arithmetic & bitwise operators to build symbolic expressions
ops = [
    ("add", "+"),
    ("sub", "-"),
    ("mul", "*"),
    ("mod", "%"),
    ("floordiv", "//"),
    ("and", "&"),
    ("or", "|"),
    ("xor", "^"),
    ("lshift", "<<"),
    ("rshift", ">>"),
]

def make_method(method, op, arg_list):
    code = f"""def {method}(self, other):
    return self._op_worker({arg_list}, lambda x, y: x {op} y, "{op}")"""
    loc = {}
    exec(code, globals(), loc)
    setattr(SymbolicInteger, method, loc[method])

for name, op in ops:
    make_method(f"__{name}__", op, "[self, other]")
    make_method(f"__r{name}__", op, "[other, self]")
