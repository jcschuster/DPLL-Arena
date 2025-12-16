#!/usr/bin/env python3
import sys
from pysat.solvers import Minisat22
from pysat.formula import CNF

input_data = sys.stdin.read()
cnf = CNF(from_string=input_data)

with Minisat22(bootstrap_with=cnf) as m:
    if m.solve():
        print("s SATISFIABLE")
    else:
        print("s UNSATISFIABLE")
    if m.get_model() is not None:
        print("v " + " ".join([str(l) for l in m.get_model()]))
