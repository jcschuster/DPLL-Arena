#!/usr/bin/env python3
import sys
import time
import random

input_data = sys.stdin.read()

sleep_time = random.uniform(0.2, 0.8)
time.sleep(sleep_time)

size = random.randint(100000, 2000000)
dummy_memory = [i for i in range(size)]

res = random.choice([1, 2])
print(f"c This is a dummy output")
print(f"s {'SATISFIABLE' if res == 1 else 'UNSATISFIABLE'}")
print(f"v 1 -2")
sys.exit(0)
