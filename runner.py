import subprocess
import re
import os
import tempfile
import shutil
import pandas as pd
import matplotlib.pyplot as plt
from pysat.formula import CNF
from pysat.solvers import Solver

# --- CONFIGURATION ---
PROBLEMS_DIR = "/app/problems"
SOLVERS_DIR = "/app/solvers"
RESULTS_DIR = "/app/results"
RESULTS_FILE = os.path.join(RESULTS_DIR, "benchmark_data.csv")

TIMEOUT_SECONDS = 30

BENCHMARK_SUITE = [
    ("Gen_Easy_1Sat", ["randkcnf", "2", "2", "1"], "UNKNOWN"),
    ("Gen_PHP_5_4", ["php", "5", "4"], "UNSAT"),
    ("Gen_Rand_3SAT_100var", ["--seed", "42", "randkcnf",
     "3", "100", "420"], "SAT"),
]


def discover_static_problems():
    """Scans /app/problems for .cnf files and adds them to the suite."""
    if not os.path.exists(PROBLEMS_DIR):
        return
    for f in os.listdir(PROBLEMS_DIR):
        if f.endswith(".cnf"):
            path = os.path.join(PROBLEMS_DIR, f)
            if f.startswith("uf"):
                expected = "SAT"
            elif f.startswith("uuf"):
                expected = "UNSAT"
            else:
                expected = "UNKNOWN"
        BENCHMARK_SUITE.append((f, path, expected))


def parse_output(stdout_str, stderr_str, exit_code):
    """Parses time, memory, status (SAT/UNSAT), and model (assignments)."""
    mem_match = re.search(
        r"Maximum resident set size \(kbytes\): (\d+)", stderr_str)
    cpu_time_match = re.search(r"User time \(seconds\): ([\d\.]+)", stderr_str)
    wall_time_match = re.search(
        r"Elapsed \(wall clock\) time.*: (\d+(?::\d+){1,2}(?:\.\d+)?)", stderr_str)
    mem_kb = int(mem_match.group(1)) if mem_match else 0
    cpu_time_sec = float(cpu_time_match.group(1)) if cpu_time_match else 0.0

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
    else:
        wall_time_sec = 0.0

    status = "ERROR"

    if exit_code == 124:
        status = "TIMEOUT"
    elif exit_code not in {0, 10, 20}:
        print(f"Warning: Solver exited with code {exit_code}")

    if "s SATISFIABLE" in stdout_str:
        status = "SAT"
    elif "s UNSATISFIABLE" in stdout_str:
        status = "UNSAT"

    model = []
    for line in stdout_str.splitlines():
        if line.startswith("v "):
            parts = line[2:].strip().split()
            for p in parts:
                if p != '0':
                    model.append(int(p))

    return mem_kb, wall_time_sec, cpu_time_sec, status, model


def verify_correctness(cnf_path, status, model, expected_result):
    """Checks if the result is correct."""

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

    if status != expected_result:
        return False, f"Wrong Result (Expected {expected_result}, Got {status})"

    if status == "SAT":
        if not model:
            return True, "SAT but no model provided"

        formula = CNF(from_file=cnf_path)
        model_set = set(model)

        for clause in formula.clauses:
            if not any(lit in model_set for lit in clause):
                return False, f"Invalid Model (Clause {clause} failed)"

        return True, "Model Verified"

    if status == "UNSAT":
        if not model:
            return True, "UNSAT but no model provided"

        formula = CNF(from_file=cnf_path)
        model_set = set(model)

        countersat = False
        for clause in formula.clauses:
            if len([*filter(lambda lit: lit not in model_set, clause)]) == 0:
                countersat = True
                break

        if countersat:
            return True, "Countermodel Verified"
        else:
            return False, "Invalid Countermodel"

    return False, "Solver Error"


def generate_plots(df):
    """Generates Time and Memory comparison charts."""
    print("Generating plots...", end=" ")

    plt.figure(figsize=(10, 6))
    pivot_time = df.pivot(
        index='problem', columns='solver', values='wall_sec')
    pivot_time.plot(kind='bar', width=0.8, rot=45, logy=True)
    plt.axhline(y=TIMEOUT_SECONDS, color='r', linestyle='--', label='Timeout')
    plt.title('Solver Execution Time (Log Scale)')
    plt.ylabel('Seconds (Log Scale)')
    plt.legend(loc='upper right')
    plt.grid(visible=True, which="both", axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'benchmark_time.png'))
    plt.close()

    plt.figure(figsize=(10, 6))
    pivot_time = df.pivot(
        index='problem', columns='solver', values='cpu_sec')
    pivot_time.plot(kind='bar', width=0.8, rot=45, logy=True)
    plt.title('Solver CPU Time (Log Scale)')
    plt.ylabel('Seconds (Log Scale)')
    plt.legend(loc='upper right')
    plt.grid(visible=True, which="both", axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'benchmark_cpu_time.png'))
    plt.close()

    plt.figure(figsize=(10, 6))
    pivot_mem = df.pivot(index='problem', columns='solver', values='memory_kb')
    (pivot_mem / 1024).plot(kind='bar', width=0.8, rot=45)  # Convert to MB
    plt.title('Solver Peak Memory Usage')
    plt.ylabel('Memory (MB)')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'benchmark_memory.png'))
    plt.close()

    print("Done! Charts saved to results folder.")


def run_benchmark():
    solvers = [f for f in os.listdir(SOLVERS_DIR) if not f.startswith('.')]
    if not solvers:
        print(f"No solvers found in {SOLVERS_DIR}.")
        return

    discover_static_problems()

    print(f"Solvers: {solvers}")
    print(f"Problems: {[p[0] for p in BENCHMARK_SUITE]}")
    print(f"Timeout Limit: {TIMEOUT_SECONDS}s")

    results = []
    print(f"Starting benchmark...")

    for prob_name, source, expected in BENCHMARK_SUITE:
        print(f"\n--- Problem: {prob_name} ---")

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.cnf') as tmp_cnf:
            if isinstance(source, list):
                subprocess.run(["cnfgen"] + source, stdout=tmp_cnf, check=True)
            else:
                shutil.copyfile(source, tmp_cnf.name)

            tmp_cnf.seek(0)

            for solver_name in solvers:
                solver_path = os.path.join(SOLVERS_DIR, solver_name)

                if solver_name.endswith(".py"):
                    base_cmd = f"python3 {solver_path}"
                elif solver_name.endswith(".ex") or solver_name.endswith(".exs"):
                    base_cmd = f"elixir {solver_path}"
                else:
                    try:
                        os.chmod(solver_path, 0o755)
                    except OSError:
                        pass
                    base_cmd = f"{solver_path}"

                cmd = f"cat {tmp_cnf.name} | /usr/bin/time -v timeout {TIMEOUT_SECONDS}s {base_cmd}"

                print(f"Running {solver_name}...", end=" ", flush=True)
                try:
                    res = subprocess.run(
                        cmd, shell=True, executable='/bin/bash', capture_output=True, text=True)

                    try:
                        mem, duration, cpu_time, status, model = parse_output(
                            res.stdout, res.stderr, res.returncode)
                    except:
                        status = "ERROR"

                    if status == "ERROR":
                        print(f"\n[DEBUG] Stderr for {solver_name}:\n{res.stderr}"
                              f"\n[DEBUG] Stdout for {solver_name}:\n{res.stdout}")

                    is_correct, note = verify_correctness(
                        tmp_cnf.name, status, model, expected)

                    print(f"[{status}] {duration}s - {note}")

                    results.append({
                        "solver": solver_name,
                        "problem": prob_name,
                        "status": status,
                        "wall_sec": duration,
                        "cpu_sec": cpu_time,
                        "memory_kb": mem,
                        "correct": is_correct,
                        "note": note
                    })
                except Exception as e:
                    print(f"Failed: {e}")

    if results:
        df = pd.DataFrame(results)
        df.to_csv(RESULTS_FILE, index=False)
        print(f"\nSaved to {RESULTS_FILE}")
        generate_plots(df)

        print("\n--- Correctness Report ---")
        report_cols = ["problem", "solver", "status", "correct",
                       "wall_sec", "cpu_sec", "note"]
        print(df[report_cols].set_index(["problem", "solver"]).to_string())
    else:
        print("No results to save")


if __name__ == "__main__":
    run_benchmark()
