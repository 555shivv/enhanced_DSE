# example_test.py
from symbolic.args import symbolic

@symbolic(a=2,b=3)
def compare(a, b):
    if a > b:
        return "a > b"
    elif a == b:
        return "a == b"
    else:
        return "a < b"

