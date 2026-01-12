from graphviz import Digraph
from ice2_ws25.ice_machine import *
from utils import generator

unique = generator()


### OPTIMIZATION ###
def optimize(iir, visual=False, debug=False):
    print("Optimizing...") if debug else None
    print("Control Flow Graph created.") if debug else None
    cfg = CFGraph(iir)
    if visual:
        cfg.visualize()
    cfg_liveness(cfg)
    print("Spilling complete.") if debug else None
    spilling(cfg)
    for x, y in zip(cfg.part, cfg.last):
        cfg.iir[x : y + 1] = reg_color(cfg.iir[x : y + 1], visual)
    print("Optimization complete.") if debug else None
    return cfg.iir


# --------- CONTROL FLOW GRAPH ---------
class CFGraph:
    def __init__(self, iir):
        self.iir = iir
        part = set()
        jump = {(None, "main")}
        labs = dict()
        for i, x in enumerate(iir):
            match x:
                case ("ifgoto", _, label):
                    jump |= {(i, label), (i, i + 1)}
                case ("goto", label):
                    jump |= {(i, label)}
                case ("label", label):
                    labs[label] = i
                case ("ret",):
                    part |= {i + 1}
        for x, y in jump.copy():
            if isinstance(y, str):
                jump -= {(x, y)}
                jump |= {(x, y := labs[y])}
            part |= {y}
            if y == 0:
                continue
            match iir[y - 1]:
                case ("goto" | "ret", *_):
                    continue
                case _:
                    jump |= {(y - 1, y)}
        self.part = sorted(part | {0})
        self.jump = dict()
        for x, y in jump:
            if not (x and y):
                continue
            self.jump.setdefault(self.part.index(x + 1) - 1, []).append(
                self.part.index(y)
            )
        self.last = [x - 1 for x in self.part[1:]] + [len(iir) - 1]

    def visualize(self):
        dot = Digraph(format="png")
        dot.attr(
            "node", fontname="FiraCode", shape="box", style="rounded", labeljust="l"
        )
        for i in range(n := len(self.part)):
            x, y = self.part[i], self.part[i + 1] if i < n - 1 else len(self.iir)
            dot.node(
                str(i), "".join([f"{tuple_to_infix(s)}\\l" for s in self.iir[x:y]])
            )
        for x, y in self.jump.items():
            for y in y:
                dot.edge(str(x), str(y))
        dot.render("dot/cfgraph", view=True)


def cfg_liveness(cfg):
    for i in range(len(iir := cfg.iir)):
        line = cfg.iir[i] = Inst(*iir[i])
        line.read = reads(line) - {"V"}
        line.write = writes(line) - {"V"}
        line.live = set()

    repeat = True
    while repeat:
        repeat = False
        for i, x in enumerate(cfg.part):
            for a in reversed(range(x + 1, cfg.last[i] + 1)):
                iir[a - 1].live |= (iir[a].live | iir[a].read) - iir[a - 1].write
            for src, dest in cfg.jump.items():
                if i in dest:
                    tmp = iir[a := cfg.last[src]].live
                    iir[a].live |= (iir[x].live | iir[x].read) - iir[a].write
                    if tmp != iir[a].live:
                        repeat = True


def reg_color(iir, visual=False):
    edges = set()
    for e in ((x, y) for line in iir for x in line.write for y in line.live):
        edges |= {tuple(sorted(e))}
    nodes = set.union(*(line.read | line.write for line in iir))
    dep = dict()
    for x, y in edges:
        dep.setdefault(x, []).append(y)
        dep.setdefault(y, []).append(x)
    stk = sorted(nodes, key=lambda x: len(dep.get(x) or []))
    col = dict()
    while stk:
        reg = stk.pop()
        adj = set(col.get(x) for x in dep.get(reg) or []) - {None}
        for i, x in enumerate(sorted(adj)):
            if i != x:
                col[reg] = i
        else:
            col[reg] = len(adj)
    if visual:
        dot = Digraph(format="png")
        dot.attr(
            "node",
            fontname="FiraCode",
            shape="circle",
            style="filled",
            fontcolor="#eff1f5",
        )
        cpal = [
            "#1e66f5",
            "#40a02b",
            "#8839ef",
            "#d20f39",
            "#fe640b",
            "#df8e1d",
            "#ea76cb",
            "#4c4f69",
        ]
        for reg in nodes:
            dot.node(str(reg), str(reg), color=cpal[col[reg] % len(cpal)])
        for x, y in edges:
            dot.edge(str(x), str(y), dir="none")
        dot.render(unique("dot/reg_color"), view=True)
    # TODO change this, because minimum doesnt work like intended on strings
    norm = {r: min(k for k, v in col.items() if v == val) for r, val in col.items()}
    return [line.replace(norm) for line in iir]


def spilling(cfg, k=4):
    """
    Führt Register-Spilling auf dem gegebenen Kontrollflussgraphen (CFG) durch.

    Implementierung basierend auf Ihrer Beschreibung:
    - Wenn Variablen ausgewählt werden zu spillen, wird am Funktionsanfang ein
    Vektor alloziert und in einem speziellen Register `RS` abgelegt.
    - Es werden drei temporäre Reserveregister verwendet (R_S0..R_S2), um
    geladene Werte temporär zu halten, wenn sie in einer Anweisung gelesen
    oder geschrieben werden.
    - An den Stellen, an denen eine gespillte Variable gelesen wird, wird
    vor der Anweisung eine Lade-Anweisung eingefügt: ("=[]", tmp, "RS", idx)
    - Wenn die Anweisung die gespillte Variable schreibt, wird nach der
    modifizierenden Anweisung eine Speicher-Anweisung eingefügt:
    ("[]=", "RS", idx, tmp)

    Hinweise:
    - Diese Implementierung benutzt neue IR-Operationen: "alloc_spill",
    "rload" und "rstore". Die restliche Pipeline (reads/writes/Inst.replace)
    muss diese eventuell erkennen bzw. behandeln.


    :param cfg: CFGraph-Objekt mit cfg.iir als Liste von Instruktionen (wird
    in-place verändert). Vor der Verwendung sollte cfg_liveness
    aufgerufen worden sein oder wir rufen es hier erneut.
    :param k: Anzahl physischer Register, die verfügbar sind.
    """
    print("Spilling...")
    # liveness wurde bereits berechnet
    iir = cfg.iir

    # Mapping: variable -> slot index in the spill vector
    spilled_map = dict()
    # Drei reservierte temporäre Register für Load/Store-Temporaries
    tmp_regs = ["R0", "R1", "R2"]

    # Hilfsfunktion: wähle Variable zum Spill (einfach heuristisch)
    def choose_var_to_spill_at_point(live_set):
        # Wähle diejenige Variable, die am häufigsten in live-sets vorkommt
        # (ein einfacher Heuristik). Andere Heuristiken sind möglich.
        return max(
            live_set,
            key=lambda v: sum((1 for line in iir if v in getattr(line, "live", set()))),
        )

    # Iterativ spillen bis an keiner Stelle mehr > k Variablen gleichzeitig live sind
    print("pre-loop")
    while True:
        # Finde einen Programmpunkt, an dem die Live-Anzahl > k
        idx = next(
            (i for i, line in enumerate(iir) if len(getattr(line, "live", set())) > k),
            None,
        )
        if idx is None:
            break  # kein Spill mehr nötig

        # Wähle eine Variable zum Spill an diesem Punkt
        var_to_spill = choose_var_to_spill_at_point(iir[idx].live)
        # Falls noch nicht gespillt, eine neue Slot-Nummer zuweisen
        if var_to_spill not in spilled_map:
            spilled_map[var_to_spill] = len(spilled_map)

        slot = spilled_map[var_to_spill]

        if isinstance(var_to_spill, list):
            var_to_spill = tuple(var_to_spill)

        # Erzeuge eine neue Instruktionsliste mit Load/Store-Einfügungen und Ersetzungen
        new_iir = []
        tmp_idx = 0
        print("var_to_spill:", var_to_spill)
        print("pre reassign register")
        for inst in iir:
            print(tmp_idx, inst)
            # Wir benutzen Inst.replace(mapping) um Register zu ersetzen.
            reads_var = var_to_spill in inst.read
            writes_var = var_to_spill in inst.write

            if reads_var:
                tmp = tmp_regs[tmp_idx % len(tmp_regs)]
                tmp_idx += 1
                # rload tmp, RS, slot
                new_iir.append(Inst("=[]", tmp, "RS", slot))
                # ersetze die gelesene Variable in der Anweisung durch tmp
                inst = inst.replace({var_to_spill: tmp})

            if writes_var and not reads_var:
                # Variable wird nur geschrieben (kein vorheriges Lesen)
                # Dann müssen wir sicherstellen, dass die Zieldestination
                # in der Instruktion durch ein temporäres Register ersetzt wird
                tmp = tmp_regs[tmp_idx % len(tmp_regs)]
                tmp_idx += 1
                inst = inst.replace({var_to_spill: tmp})
                # Füge die modifizierende Instruktion ein
                new_iir.append(inst)
                # rstore RS, slot, tmp
                new_iir.append(Inst("[]=", "RS", slot, tmp))
                print(*[str(x) for x in new_iir], sep="\n")
                continue

            if writes_var and reads_var:
                # Fall: x = x + ..  (zuerst geladen, dann geschrieben)
                # Wir haben die Variable oben bereits durch tmp ersetzt, also
                # schreiben wir nach der Instruktion zurück in den Spill-Slot.
                new_iir.append(inst)
                tmp = tmp_regs[(tmp_idx - 1) % len(tmp_regs)]
                new_iir.append(Inst("[]=", "RS", slot, tmp))
                continue

            # Kein Bezug zur gespillten Variable -> einfach kopieren
            new_iir.append(inst)
        print(*[str(x) for x in new_iir], sep="\n")
        print("post reassign register")

        # Recompute read/write/live for die neuen Instruktionen
        print("pre-recomp-liveness")
        cfg_liveness(cfg)
        print("post-recomp-liveness")

        # Continue the outer while loop: falls noch Stellen mit live>k existieren,
        # wird eine neue Variable zum Spillen gewählt.
    print("post-loop")

    # Wenn wir gespillt haben, füge am Funktionsanfang die Allokation des Vektors ein
    if spilled_map:
        alloc_inst = Inst("mk[]", "RS", len(spilled_map))
        cfg.iir.insert(0, alloc_inst)

        # Nach dem Einfügen der Allokation müssen wir ggf. part/last/jump anpassen.
        # Hier vereinfachend: wir setzen alle Metadaten zurück und lassen den
        # Aufrufer (oder einen weiteren Pass) die CFG neu aufbauen falls nötig.

    print(f"Spilled variables: {spilled_map}")
    return cfg.iir
    # print("Spilling...")
    # for i in range(len(iir := cfg.iir)):
    #     line = cfg.iir[i] = Inst(*iir[i])
    #     line.read = reads(line) - {"V"}
    #     line.write = writes(line) - {"V"}
    #     line.live = set()
    #
    # repeat = True
    # while repeat:
    #     repeat = False
    #     for i, x in enumerate(cfg.part):
    #         for a in reversed(range(x + 1, cfg.last[i] + 1)):
    #             iir[a - 1].live |= (iir[a].live | iir[a].read) - iir[a - 1].write
    #         for src, dest in cfg.jump.items():
    #             if i in dest:
    #                 tmp = iir[a := cfg.last[src]].live
    #                 iir[a].live |= (iir[x].live | iir[x].read) - iir[a].write
    #                 if tmp != iir[a].live:
    #                     repeat = True
    #
    # for i in range(len(iir)):
    #     while len(iir[i].live) > k:
    #         var_to_spill = next(iter(iir[i].live))
    #         iir[i].live.remove(var_to_spill)
    #         # Insert load before instruction


#  --------- REGISTER ALLOCATION (GRAPH COLORING) ---------


# MIME
# def find_labels(tac):
#     labels = {}
#     for i, instruction in enumerate(tac):
#         match instruction:
#             case ("label", target_l):
#                 labels[target_l] = i
#     return labels
#
#
# def control_flow_graph(tac):
#     """
#     Erstellt einen Kontrollflussgraphen (CFG) aus dem gegebenen dreistelligen Zwischencode (TAC).
#     :param tac: Liste von TAC-Anweisungen
#     :return: Kontrollflussgraph als Dictionary
#     """
#     cfg = {}
#     labels = find_labels(tac)
#
#     for i, instruction in enumerate(tac):
#         match instruction:
#             case ("goto", target_l):
#                 cfg[i] = [labels[target_l]]
#             case ("ifgoto", _, target_l):
#                 cfg[i] = []
#                 if i + 1 < len(tac):
#                     cfg[i].append(i + 1)
#                 cfg[i].append(labels[target_l])
#             case _:
#                 cfg[i] = []
#                 if i + 1 < len(tac):
#                     cfg[i].append(i + 1)
#
#     return cfg
#

# network X - coloring algorithmus
# def basis_block(n_instructions, tac):
#     """
#     Teilt den Kontrollflussgraphen in Basisblöcke auf.
#     :param cfg: Kontrollflussgraph als Dictionary
#     :param n_instructions: Anzahl der TAC-Instruktionen
#     :return: Liste von Basisblöcken (Start-, Endindex)
#     """
#     leaders = {0}
#     labels = {}
#
#     for i, instr in enumerate(tac):
#         match instr:
#             case ("label", target_l):
#                 labels[target_l] = i
#
#     for i, instr in enumerate(tac):
#         match instr:
#             case ("goto", target_l):
#                 if i + 1 < n_instructions:
#                     leaders.add(i + 1)
#                 leaders.add(labels[target_l])
#             case ("ifgoto", _, target_l):
#                 if i + 1 < n_instructions:
#                     leaders.add(i + 1)
#                 leaders.add(labels[target_l])
#             case _:
#                 continue
#
#     leaders = sorted(leaders)
#     blocks = []
#     for i in range(len(leaders)):
#         start = leaders[i]
#         end = leaders[i + 1] if i + 1 < len(leaders) else n_instructions
#         blocks.append((start, end))
#
#     return blocks
#


# def register_coloring(cfg, tac):
#     """
#     Führt eine einfache Register-Allokation basierend auf Lebendigkeitsanalyse durch.
#     :param cfg: Kontrollflussgraph als Dictionary
#     :param tac: Liste von TAC-Anweisungen
#     :return: Mapping von Registern zu reduzierten Registern
#     """
#     in_sets, out_sets = liveness2(cfg, tac)
#     interference_graph = {}
#
#     n_instructions = infer_n_instructions(cfg)
#     for i in range(n_instructions):
#         live_vars = out_sets[i].union(in_sets[i])
#         for var1 in live_vars:
#             if var1 not in interference_graph:
#                 interference_graph[var1] = set()
#             for var2 in live_vars:
#                 if var1 != var2:
#                     interference_graph[var1].add(var2)
#
#     coloring = {}
#
#     for var in sorted(
#         interference_graph, key=lambda v: len(interference_graph[v]), reverse=True
#     ):
#         neighbor_colors = {
#             coloring.get(neigh)
#             for neigh in interference_graph[var]
#             if neigh in coloring
#         }
#         color = 0
#         while color in neighbor_colors:
#             color += 1
#         coloring[var] = color
#
#     return coloring
#
#
# def assign_regs(tac, coloring):
#     """
#     Weist den TAC-Anweisungen die zugewiesenen Register zu.
#     :param tac: Liste von TAC-Anweisungen
#     :param coloring: Mapping von Variablen zu Registern
#     :return: TAC mit zugewiesenen Registern
#     """
#     print(tac)
#     print(coloring)
#     assigned_tac = []
#
#     for instruction in tac:
#         new_instruction = []
#         for part in instruction:
#             if isinstance(part, str) and part in coloring:
#                 new_instruction.append(f"R{coloring[part]}")
#             else:
#                 new_instruction.append(part)
#         assigned_tac.append(tuple(new_instruction))
#
#     print("\nTAC mit zugewiesenen Registern:")
#     for line_no, instr in enumerate(assigned_tac):
#         print(f"{line_no:02}: {instr}")
#
#     return assigned_tac


#  --------- CONSTANT FOLDING ---------
def constant_folding(tac):
    """
    Führt Constant Folding auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit gefalteten Konstanten
    """
    optimized_tac = []

    for instruction in tac:
        match instruction:
            case (op, target, arg1, arg2) if op in {"+", "-", "*", "/"}:
                if isinstance(arg1, int) and isinstance(arg2, int):
                    if op == "+":
                        result = arg1 + arg2
                    elif op == "-":
                        result = arg1 - arg2
                    elif op == "*":
                        result = arg1 * arg2
                    elif op == "/":
                        result = arg1 // arg2  # Ganzzahlige Division
                    optimized_tac.append(("=", target, result))
                else:
                    optimized_tac.append(instruction)
            case _:
                optimized_tac.append(instruction)

    return optimized_tac


#  --------- COMMON SUBEXPRESSION ELIMINATION ---------
def common_subexpression_elimination(tac):
    """
    Führt Common Subexpression Elimination auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit eliminierten gemeinsamen Teilausdrücken
    """
    optimized_tac = []
    expr_table = {}

    for instruction in tac:
        match instruction:
            case (op, target, arg1, arg2) if op in {"+", "-", "*", "/"}:
                expr = (op, arg1, arg2)
                if expr in expr_table:
                    optimized_tac.append(("=", target, expr_table[expr]))
                else:
                    expr_table[expr] = target
                    optimized_tac.append(instruction)
            case _:
                optimized_tac.append(instruction)

    return optimized_tac


#  --------- COPY PROPAGATION ---------
def copy_propagation(tac):
    """
    Führt Copy Propagation auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit propagierten Kopien
    """
    optimized_tac = []
    copy_table = {}

    for instruction in tac:
        match instruction:
            case ("=", target, source):
                if source in copy_table:
                    copy_table[target] = copy_table[source]
                else:
                    copy_table[target] = source
                optimized_tac.append(instruction)
            case _:
                new_instruction = []
                for part in instruction:
                    if isinstance(part, str) and part in copy_table:
                        new_instruction.append(copy_table[part])
                    else:
                        new_instruction.append(part)
                optimized_tac.append(tuple(new_instruction))

    return optimized_tac


#  --------- DEAD CODE ELIMINATION ---------
def dead_code_elimination(tac):
    """
    Führt Dead Code Elimination auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit eliminiertem totem Code
    """
    optimized_tac = []
    used_vars = set()

    for instruction in reversed(tac):
        match instruction:
            case ("=", target, source):
                if target in used_vars:
                    optimized_tac.append(instruction)
                    if isinstance(source, str):
                        used_vars.add(source)
                else:
                    continue
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
                if target in used_vars:
                    optimized_tac.append(instruction)
                    if isinstance(arg1, str):
                        used_vars.add(arg1)
                    if isinstance(arg2, str):
                        used_vars.add(arg2)
                else:
                    continue
            case _:
                optimized_tac.append(instruction)

    optimized_tac.reverse()
    return optimized_tac


#  --------- LOOP INVARIANT CODE MOTION ---------
def loop_invariant_code_motion(tac):
    """
    Führt Loop Invariant Code Motion auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit verschobenem loop-invariantem Code
    """
    optimized_tac = []
    loop_invariants = []

    in_loop = False
    for instruction in tac:
        match instruction:
            case ("label", label) if label.startswith("loop_start"):
                in_loop = True
                optimized_tac.append(instruction)
            case ("label", label) if label.startswith("loop_end"):
                in_loop = False
                optimized_tac.append(instruction)
                optimized_tac.extend(loop_invariants)
                loop_invariants.clear()
            case (op, target, arg1, arg2) if op in {"+", "-", "*", "/"}:
                if in_loop and isinstance(arg1, int) and isinstance(arg2, int):
                    loop_invariants.append(instruction)
                else:
                    optimized_tac.append(instruction)
            case _:
                optimized_tac.append(instruction)

    return optimized_tac


#  --------- STRENGTH REDUCTION ---------
def strength_reduction(tac):
    """
    Führt Strength Reduction auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit reduzierter Rechenstärke
    """
    optimized_tac = []

    for instruction in tac:
        match instruction:
            case ("*", target, arg1, arg2):
                if isinstance(arg2, int) and arg2 == 2:
                    optimized_tac.append(("+", target, arg1, arg1))
                else:
                    optimized_tac.append(instruction)
            case _:
                optimized_tac.append(instruction)

    return optimized_tac
