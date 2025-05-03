# quick_test.py

import sys, os

# 1) Make sure current directory is on the import path
sys.path.insert(0, os.path.abspath("."))

# 2) Import from the 'symbolic' package
from symbolic.symbolic_types.symbolic_int import SymbolicInteger
from symbolic.symbolic_types.symbolic_type import SymbolicObject

# 3) Monkey-patch for debug
def dbg_gt(self, other):
    print(f"[DEBUG __gt__] comparing {self.val} > {other.val}")
    return SymbolicObject.__gt__(self, other)

def dbg_bool(self):
    print(f"[DEBUG __bool__] on {self.toString()}")
    return SymbolicObject.__bool__(self)

SymbolicInteger.__gt__   = dbg_gt
SymbolicInteger.__bool__ = dbg_bool

# 4) Create two symbolic ints and test
a = SymbolicInteger("a", 0)
b = SymbolicInteger("b", 0)

print("Raw comparison object:", (a > b))
print("Boolean of comparison:", bool(a > b))
