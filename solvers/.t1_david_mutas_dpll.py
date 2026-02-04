import sys
from typing import Set, FrozenSet, Tuple, Dict

Clause = FrozenSet[int]
Formula = Set[Clause]

Assignment = Dict[int, bool]


# Extrahiert die Variable aus einem Literal
# Beispiel: var(-3) -> 3
def var(lit: int) -> int:
    return abs(lit)


# Negiert ein Literal
# Beispiel: neg(2) -> -2, neg(-5) -> 5
def neg(lit: int) -> int:
    return -lit


# Prüft ob die Formel gelöst ist (keine Klauseln mehr übrig)
def _is_solved(formula: Formula) -> bool:
    return len(formula) == 0


# Wendet Zuweisung eines Literals auf gesamte Formel an
def _assign_literal(formula: Formula, lit: int) -> Tuple[Formula, bool]:
    new_formula: Formula = set()

    for clause in formula:
        # 1) Klausel enthält Literal --> Klausel ist wahr, fertig
        if lit in clause:
            continue

        # 2) Klausel enthält Negation des Literals --> Aus Klausel entfernen
        if neg(lit) in clause:
            new_clause = set()
            for l in clause:
                if l != neg(lit):
                    new_clause.add(l)
            new_clause = frozenset(new_clause)
            
            # 2a) Entfernen bildet leere Klausel --> Konflikt
            if len(new_clause) == 0:
                return set(), True
            
            new_formula.add(new_clause)
            continue

        # 3) Literal nicht in Klausel vorhanden, keine Änderungen an Klausel vornehmen
        new_formula.add(clause)

    # Kein Konflikt entstanden
    return new_formula, False

# Finde alle Klauseln mit genau einem Literal, setze das Literal auf TRUE
def _unit_propagate(formula: Formula, assignment: Assignment) -> Tuple[Formula, Assignment, bool]:
    formula = set(formula)
    assignment = dict(assignment)

    while True:
        # Finde alle Unit-Klauseln (Klauseln mit genau einem Literal)
        unit_literals = []
        for clause in formula:
            if len(clause) == 1:
                for lit in clause:
                    unit_literals.append(lit)

        if len(unit_literals) == 0:
            break

        for lit in unit_literals:
            v = var(lit)
            v_sign = (lit > 0)

            if v in assignment:
                # Assignment ist inkonsistent --> Konflikt
                if assignment[v] != v_sign:
                    return set(), {}, True
                # Assignment ist konsistent --> fertig, nächstes Literal überprüfen
                continue
            # Literal noch nicht assigned --> wird mit v_sign assigned
            assignment[v] = v_sign
            formula, conflict = _assign_literal(formula, lit)
            if conflict:
                return set(), {}, True

            # nach Literal-Assignment wird von vorne überprüft
            break
        else:
            # For-loop endet ohne eine neue Zuweisung eines Literals. Unit propagation beendet
            break

    return formula, assignment, False


# Findet alle Pure Literals und weist sie zu
def _pure_literal_elimination(formula: Formula, assignment: Assignment) -> Tuple[Formula, Assignment]:
    formula = set(formula)
    assignment = dict(assignment)
    
    while True:
        # Sammle alle Literale in der Formel
        positive_literals = set()  # Variablen die positiv vorkommen
        negative_literals = set()  # Variablen die negativ vorkommen
        
        for clause in formula:
            for lit in clause:
                v = var(lit)
                if lit > 0:
                    positive_literals.add(v)
                else:
                    negative_literals.add(v)
        
        # Finde Pure Literals
        pure_literals = []
        
        # Variablen die NUR positiv vorkommen
        for v in positive_literals:
            if v not in negative_literals and v not in assignment:
                pure_literals.append(v)  # Positives Literal
        
        # Variablen die NUR negativ vorkommen
        for v in negative_literals:
            if v not in positive_literals and v not in assignment:
                pure_literals.append(neg(v))  # Negatives Literal
        
        if len(pure_literals) == 0:
            break
        
        # Weise alle Pure Literals zu
        for lit in pure_literals:
            v = var(lit)
            v_sign = (lit > 0)
            assignment[v] = v_sign
            formula, _ = _assign_literal(formula, lit)  # Kann keinen Konflikt verursachen
    
    return formula, assignment


# Wählt eine unzugewiesene Variable aus der Formel
def _choose_variable(formula: Formula, assignment: Assignment) -> int:
    for clause in formula:
        for lit in clause:
            v = var(lit)
            if v not in assignment:
                return v
    return 0  # Sollte nie passieren, wenn Formel nicht leer ist


# DPLL Algorithmus - Hauptfunktion
# Gibt zurück: (erfüllbar, assignment)
def dpll(formula: Formula, assignment: Assignment) -> Tuple[bool, Assignment]:
    # 1) Prüfe ob Formel bereits gelöst (leer = alle Klauseln erfüllt)
    if _is_solved(formula):
        return True, assignment
    
    # 2) Pure Literal Elimination
    formula, assignment = _pure_literal_elimination(formula, assignment)
    
    # 3) Nach Pure Literal Elimination prüfen ob gelöst
    if _is_solved(formula):
        return True, assignment
    
    # 4) Unit Propagation
    formula, assignment, conflict = _unit_propagate(formula, assignment)
    if conflict:
        return False, {}
    
    # 5) Nach Unit Propagation nochmal prüfen ob gelöst
    if _is_solved(formula):
        return True, assignment
    
    # 6) Wähle eine Variable zum Splitten
    v = _choose_variable(formula, assignment)
    
    # 7) Split: Versuche v = True
    new_assignment = dict(assignment)
    new_assignment[v] = True
    new_formula, conflict = _assign_literal(formula, v)
    if not conflict:
        sat, result_assignment = dpll(new_formula, new_assignment)
        if sat:
            return True, result_assignment
    
    # 8) Split: v = True hat nicht funktioniert, versuche v = False
    new_assignment = dict(assignment)
    new_assignment[v] = False
    new_formula, conflict = _assign_literal(formula, neg(v))
    if not conflict:
        sat, result_assignment = dpll(new_formula, new_assignment)
        if sat:
            return True, result_assignment
    
    # 9) Beide Splits gescheitert --> UNSAT
    return False, {}


# Liest DIMACS CNF von einem String und gibt die Formel zurück
def parse_dimacs(input_str: str) -> Formula:
    formula: Formula = set()
    
    for line in input_str.split('\n'):
        line = line.strip()
        
        # Leere Zeilen überspringen
        if len(line) == 0:
            continue
        
        # Kommentare überspringen (beginnen mit 'c')
        if line[0] == 'c':
            continue
        
        # Problem-Zeile überspringen (beginnt mit 'p')
        if line[0] == 'p':
            continue
        
        # Klausel einlesen
        literals = []
        parts = line.split()
        for part in parts:
            num = int(part)
            if num == 0:
                break  # Ende der Klausel
            literals.append(num)
        
        if len(literals) > 0:
            clause = frozenset(literals)
            formula.add(clause)
    
    return formula


# Hauptprogramm - liest von stdin und führt DPLL aus
def main():
    # Lese gesamte Eingabe von stdin
    input_str = sys.stdin.read()
    formula = parse_dimacs(input_str)
    
    sat, assignment = dpll(formula, {})
    
    if sat:
        print("s SATISFIABLE")
        # Ausgabe der Variablenbelegung
        model_parts = []
        for v in sorted(assignment.keys()):
            if assignment[v]:
                model_parts.append(str(v))
            else:
                model_parts.append(str(neg(v)))
        model_parts.append("0")
        print("v " + " ".join(model_parts))
    else:
        print("s UNSATISFIABLE")


if __name__ == "__main__":
    main()