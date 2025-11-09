def control_flow(tac):
    """
    Erstellt einen Kontrollflussgraphen (CFG) aus dem gegebenen dreistelligen Zwischencode (TAC).
    :param tac: Liste von TAC-Anweisungen
    :return: Kontrollflussgraph als Dictionary
    """
    cfg = {}
    labels = {}

    for i, instruction in enumerate(tac):
        match instruction:
            case ("label", target_l):
                labels[target_l] = i

    for i, instruction in enumerate(tac):
        match instruction:
            case ("goto", target_l):
                cfg[i] = [labels[target_l]]
            case ("ifgoto", _, target_l):
                cfg[i] = []
                if i + 1 < len(tac):
                    cfg[i].append(i + 1)
                cfg[i].append(labels[target_l])
            case _:
                cfg[i] = []
                if i + 1 < len(tac):
                    cfg[i].append(i + 1)

    return cfg


# network X - coloring algorithmus


def basis_block(n_instructions, tac):
    """
    Teilt den Kontrollflussgraphen in Basisblöcke auf.
    :param cfg: Kontrollflussgraph als Dictionary
    :param n_instructions: Anzahl der TAC-Instruktionen
    :return: Liste von Basisblöcken (Start-, Endindex)
    """
    leaders = {0}
    labels = {}

    for i, instr in enumerate(tac):
        match instr:
            case ("label", target_l):
                labels[target_l] = i

    for i, instr in enumerate(tac):
        match instr:
            case ("goto", target_l):
                if i + 1 < n_instructions:
                    leaders.add(i + 1)
                leaders.add(labels[target_l])
            case ("ifgoto", _, target_l):
                if i + 1 < n_instructions:
                    leaders.add(i + 1)
                leaders.add(labels[target_l])
            case _:
                continue

    leaders = sorted(leaders)
    blocks = []
    for i in range(len(leaders)):
        start = leaders[i]
        end = leaders[i + 1] if i + 1 < len(leaders) else n_instructions
        blocks.append((start, end))

    return blocks


def infer_n_instructions(cfg):
    all_indices = set(cfg.keys())
    for targets in cfg.values():
        all_indices.update(targets)
    return max(all_indices) + 1 if all_indices else 0


def liveness(cfg, tac):
    """
    Führt eine Lebendigkeitsanalyse auf dem Kontrollflussgraphen durch.
    :param cfg: Kontrollflussgraph als Dictionary
    :param tac: Liste von TAC-Anweisungen
    :return: Lebendigkeitsinformationen als Dictionary
    """
    n_instructions = infer_n_instructions(cfg)
    in_sets = {i: set() for i in range(n_instructions)}
    out_sets = {i: set() for i in range(n_instructions)}

    def uses_defs(instruction):
        uses = set()
        defs = set()
        match instruction:
            case ("=", target, source):
                defs.add(target)
                if isinstance(source, str):
                    uses.add(source)
            case (op, target, arg1, arg2) if op in {
                "+",
                "-",
                "*",
                "/",
                "<=",
                "<",
                ">=",
                ">",
                "==",
                "!=",
            }:
                defs.add(target)
                if isinstance(arg1, str):
                    uses.add(arg1)
                if isinstance(arg2, str):
                    uses.add(arg2)
            case ("[]=", _, index, value):
                if isinstance(index, str):
                    uses.add(index)
                if isinstance(value, str):
                    uses.add(value)
            case _:
                pass
        return uses, defs

    changed = True
    while changed:
        changed = False
        for i in reversed(range(n_instructions)):
            old_in = in_sets[i].copy()
            old_out = out_sets[i].copy()

            out_sets[i] = set()
            for succ in cfg.get(i, []):
                out_sets[i].update(in_sets[succ])

            uses, defs = uses_defs(tac[i])
            in_sets[i] = uses.union(out_sets[i] - defs)

            if old_in != in_sets[i] or old_out != out_sets[i]:
                changed = True

    return in_sets, out_sets


def register_coloring(cfg, tac):
    """
    Führt eine einfache Register-Allokation basierend auf Lebendigkeitsanalyse durch.
    :param cfg: Kontrollflussgraph als Dictionary
    :param tac: Liste von TAC-Anweisungen
    :return: Mapping von Variablen zu Registern
    """
    in_sets, out_sets = liveness(cfg, tac)
    interference_graph = {}

    n_instructions = infer_n_instructions(cfg)
    for i in range(n_instructions):
        live_vars = in_sets[i].union(out_sets[i])
        for var1 in live_vars:
            if var1 not in interference_graph:
                interference_graph[var1] = set()
            for var2 in live_vars:
                if var1 != var2:
                    interference_graph[var1].add(var2)

    registers = ["R1", "R2", "R3", "R4"]
    coloring = {}
    for var in interference_graph:
        neighbor_colors = {
            coloring.get(neigh)
            for neigh in interference_graph[var]
            if neigh in coloring
        }
        for reg in registers:
            if reg not in neighbor_colors:
                coloring[var] = reg
                break

    return coloring


if __name__ == "__main__":
    example = [
        ("label", "main"),
        ("=", "i", 1),
        ("label", "loop_start0"),
        ("=", "j", 1),
        ("label", "loop_start1"),
        ("*", "t1", 10, "i"),
        ("+", "t2", "t1", "j"),
        ("*", "t3", 8, "t2"),
        ("-", "t4", "t3", 88),
        ("[]=", "a", "t4", "i"),
        ("+", "j", "j", 1),
        ("<=", "t0", "j", 10),
        ("ifgoto", "t0", "loop_start1"),
        ("+", "i", "i", 1),
        ("<=", "t0", "i", 10),
        ("ifgoto", "t0", "loop_start0"),
        ("=", "i", 1),
        ("label", "loop_start2"),
        ("-", "t5", "i", 1),
        ("*", "t6", "t5", 88),
        ("[]=", "a", "t6", 1),
        ("+", "i", "i", 1),
        ("<=", "t0", "i", 10),
        ("ifgoto", "t0", "loop_start2"),
    ]
    cfg = control_flow(example)
    bloecke = basis_block(infer_n_instructions(cfg), example)
    print("Basisblöcke:")
    for start, end in bloecke:
        print(f"Block von {start} bis {end}")

    # Kontrollflussgraph ausgeben
    print("\nKontrollflussgraph:")
    for line_no, instr in enumerate(example):
        print(f"{line_no:02}: {instr} -> {cfg.get(line_no, [])}")

    # Lebendigkeitsanalyse
    in_sets, out_sets = liveness(cfg, example)
    print("\nLebendigkeitsanalyse:")
    for i in range(infer_n_instructions(cfg)):
        print(f"Instr {i:02}: IN={in_sets[i]} OUT={out_sets[i]}")

    # Register-Allokation
    coloring = register_coloring(cfg, example)
    print("\nRegister-Allokation:")
    for var, reg in coloring.items():
        print(f"Variable {var} -> Register {reg}")


# Lokale Optimierung
# neue var als blatt

# Globale Optimierung
# Über die Bassiblöcke hinweg
# Semantik wird nicht verändert
# common subexpression elimination
# copy propagation
# dead code elimination
# constant folding
# loop invariant code motion
# strength reduction
#
# Digraph
# gravis
