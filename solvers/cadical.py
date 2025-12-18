#!/usr/bin/env python3
import sys
from pysat.solvers import Cadical195
from pysat.formula import CNF

input_data = sys.stdin.read()
cnf = CNF(from_string=input_data)

with Cadical195(bootstrap_with=cnf) as c:
    if c.solve():
        print("s SATISFIABLE")
    else:
        print("s UNSATISFIABLE")
    if c.get_model() is not None:
        print("v " + " ".join([str(l) for l in c.get_model()]))
