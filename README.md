# AISE-LKR: DPLL-Arena

## Usage

Put your provers in the folder `solver` in a format that is executable via `./<your_solver>` or as a single Python or Elixir file. If you build an executable, please make sure that it is compatible with Linux (e.g., in Windows, use WSL). After building and running the application, the results can be found in CSV-format and as visualization in the folder `results`. If your solver is not in binary format (i.e., a .py or a .exs file), make sure that your program uses _LF_ characters, not _CRLF_ (Windows standard) or _CR_ (MacOS standard)!

## Input and Output Format

Your prover should **read a string from stdin** in DIMACS-syntax that represents a SAT problem in clause normal form (CNF) (separated by `\n` characters). This string is guaranteed to fulfil the requirements given in the provided paper on DIMACS (variable occurrence etc.).

The system expects one of two outputs:

-   `s SATISFIABLE` means that the prover can satisfy the problem. A variable assignment can be given with an additional line `v <VARIABLES>` where `<VARIABLES>` contains of positive and negative numbers representing the assignment (true or false) to the respective variable and may end in "0" (e.g., `v 1 -2 3 0`). Note that the correctness of the model will be checked by the system.
-   `s UNSATISFIABLE` means that the prover can't find a variable assignment that satisfies the problem. A model (`v <VARIABLES>`) can also be given in the same fashion.

## Build the image

`docker build -t sat-bench .`

## Run the benchmark

On Windows:

`docker run --rm -v "${PWD}/solvers:/app/solvers" -v "${PWD}/results:/app/results" -v "${PWD}/problems:/app/problems" sat-bench`

On Unix systems (Linux, MacOS):

`docker run --rm -v "$(pwd)/solvers:/app/solvers" -v "$(pwd)/results:/app/results" -v "$(pwd)/problems:/app/problems" sat-bench`

## Run the web-app containing stats

On Windows:

`docker run --rm -p 8501:8501 -v "${pwd}/results:/app/results" --entrypoint streamlit sat-bench run /app/dashboard.py --server.address=0.0.0.0`

On Unix systems (Linux, MacOS):

`docker run --rm -p 8501:8501 -v "$(pwd)/results:/app/results" --entrypoint streamlit sat-bench run /app/dashboard.py --server.address=0.0.0.0`
