import subprocess
import re
import time
from pysat.formula import CNF
from pysat.solvers import Solver

TIMEOUT_SECONDS: int = 30


def verify_dimacs(file_path: str) -> bool:
    """Verifies if the file is valid DIMACS CNF."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        literals: set[int] = set()
        nbvars = 0
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("c"):
                continue
            elif line.startswith("p"):
                parts = line.split()
                if len(parts) >= 3:
                    nbvars = int(parts[2])
            else:
                literals = literals.union({abs(int(l))
                                          for l in line.split()[:-1]})
        if nbvars > 0 and literals:
            return all(l > 0 for l in literals) and all(l <= nbvars for l in literals)
        return True
    except Exception as e:
        print(f"Verification error: {e}")
        return False


def parse_output(stdout_str, stderr_str, exit_code, wall_time_sec=0.0, cpu_time_sec=0.0):
    """Parses memory, status (SAT/UNSAT), and model (assignments).
    Times are passed in as parameters for higher precision.
    wall_time_sec and cpu_time_sec are in seconds.
    """
    mem_match = re.search(
        r"Maximum resident set size \(kbytes\): (\d+)", stderr_str)
    mem_kb = int(mem_match.group(1)) if mem_match else 0

    # If times weren't provided, try to parse from stderr (lower precision)
    if wall_time_sec == 0.0:
        wall_time_match = re.search(
            r"Elapsed \(wall clock\) time.*: (\d+(?::\d+){1,2}(?:\.\d+)?)", stderr_str)
        wall_time_str = wall_time_match.group(1) if wall_time_match else None
        if wall_time_str:
            parts = wall_time_str.split(':')
            try:
                if len(parts) == 3:
                    h = int(parts[0])
                    m = int(parts[1])
                    s = float(parts[2])
                elif len(parts) == 2:
                    h = 0
                    m = int(parts[0])
                    s = float(parts[1])
                else:
                    raise ValueError("Unexpected time format")
                wall_time_sec = h * 3600 + m * 60 + s
            except (ValueError, TypeError):
                wall_time_sec = 0.0

    if cpu_time_sec == 0.0:
        cpu_time_match = re.search(
            r"User time \(seconds\): ([\d\.]+)", stderr_str)
        cpu_time_sec = float(cpu_time_match.group(1)
                             ) if cpu_time_match else 0.0

    wall_time_ms = wall_time_sec * 1000
    cpu_time_ms = cpu_time_sec * 1000

    status = "ERROR"

    if exit_code == 124:
        status = "TIMEOUT"
    elif exit_code not in {0, 10, 20}:
        print(f"Warning: Solver exited with code {exit_code}", flush=True)

    if "s SATISFIABLE" in stdout_str:
        status = "SAT"
    elif "s UNSATISFIABLE" in stdout_str:
        status = "UNSAT"

    model = None
    for line in stdout_str.splitlines():
        if line.startswith("v "):
            model = []
            parts = line[2:].strip().split()
            for p in parts:
                if p != '0':
                    model.append(int(p))
            break

    return mem_kb, wall_time_ms, cpu_time_ms, status, model


def verify_correctness(cnf_path, status, model, expected_result):
    """Checks if the result is correct."""

    if status == "TIMEOUT":
        return False, "TIMEOUT"

    if expected_result == "UNKNOWN":
        solver = Solver()
        formula = CNF(from_file=cnf_path)
        solver.append_formula(formula)
        match solver.solve():
            case True: "SAT"
            case False: "UNSAT"
            case None: "UNKNOWN"
        if solver.solve():
            expected_result = "SAT"
        else:
            expected_result = "UNSAT"

    if expected_result != "UNKNOWN" and status != expected_result:
        return False, f"Wrong Result (Expected {expected_result}, Got {status})"

    if status == "SAT":
        if model is None:
            return True, "SAT (no model given)"

        formula = CNF(from_file=cnf_path)
        model_set = set(model)

        for clause in formula.clauses:
            if not any(lit in model_set for lit in clause):
                return False, f"Invalid Model (Clause {clause} failed)"

        return True, "SAT (given model verified)"

    if status == "UNSAT":
        return True, "UNSAT"

    return False, "Solver Error"


def run_solver(solver_path, cnf_path):
    """Executes a single solver on a single CNF file with high-precision timing."""
    cmd = f"cat {cnf_path} | /usr/bin/time -v timeout {TIMEOUT_SECONDS}s {solver_path}"

    if solver_path.endswith(".py"):
        cmd = f"cat {cnf_path} | /usr/bin/time -v timeout {TIMEOUT_SECONDS}s python3 {solver_path}"
    elif solver_path.endswith(".ex") or solver_path.endswith(".exs"):
        cmd = f"cat {cnf_path} | /usr/bin/time -v timeout {TIMEOUT_SECONDS}s elixir {solver_path}"

    try:
        wall_start = time.perf_counter()
        res = subprocess.run(
            cmd, shell=True, executable='/bin/bash', capture_output=True, text=True
        )
        wall_end = time.perf_counter()
        wall_time_sec = round(wall_end - wall_start, 4)

        cpu_time_match = re.search(
            r"User time \(seconds\): ([\d\.]+)", res.stderr)
        cpu_time_sec = float(cpu_time_match.group(1)
                             ) if cpu_time_match else 0.0

        return res.stdout, res.stderr, res.returncode, wall_time_sec, cpu_time_sec
    except Exception as e:
        return "", str(e), 1, 0.0, 0.0
