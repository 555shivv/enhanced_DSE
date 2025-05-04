from lib.bsearch import *
from symbolic.args import symbolic



array = [ 0, 4, 6, 95, 430, 4944, 119101 ]
@symbolic(k=0)
def binary_search(k):
	i = bsearch(array,k)
	if(i>=0):
		if (not array[i]==k):
			return "ERROR"
		else:
			return str(k)
	else:
		if (k in array):
			return "ERROR"
		else:
			return "NOT_FOUND"
def expected_result():
    return [str(x) for x in array] + ["NOT_FOUND"]


