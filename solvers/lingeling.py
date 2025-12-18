#!/usr/bin/env python3
import sys
from pysat.solvers import Lingeling
from pysat.formula import CNF

input_data = sys.stdin.read()
cnf = CNF(from_string=input_data)

with Lingeling(bootstrap_with=cnf) as l:
    if l.solve():
        print("s SATISFIABLE")
    else:
        print("s UNSATISFIABLE")
    if l.get_model() is not None:
        print("v " + " ".join([str(lit) for lit in l.get_model()]))
