import sys

input_data = sys.stdin.read()


def verify_dimacs() -> bool:
    literals = set()
    nbvars = 0
    for line in input_data.splitlines():
        line = line.strip()
        if line.startswith("c"):
            continue
        elif line.startswith("p"):
            nbvars = int(line.split()[2])
        else:
            literals = literals.union(
                {abs(int(l)) for l in line.split()[:-1]})
    if all(l > 0 for l in literals) and all(l in literals for l in range(1, nbvars+1)):
        print("verified!")
        return True
    else:
        print("could not be verified!")
        return False


if __name__ == "__main__":
    verify_dimacs()
