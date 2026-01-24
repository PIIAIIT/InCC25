from graphviz import Digraph
from ice2_ws25.ice_machine import (
    Inst,
    reads,
    writes,
    reassign_registers,
    tuple_to_infix,
)
from utils import generator

unique = generator()


def optimize(iir, config={}):
    """
    Führt Optimierungen auf dem gegebenen Control Flow Graph (CFG) durch.
    Aktuell implementierte Optimierungen:
    - Register-Allokation mit Spilling

    Args:
        cfg: Control Flow Graph
        visual: Ob der CFG visualisiert werden soll
        debug: Ob Debug-Informationen ausgegeben werden sollen

    Returns:
        Optimierte Instruktionsliste
    """
    print("Starte Optimierung...") if config.debug else None

    cfg = CFGraph(iir)
    liveness(cfg)

    if config.debug:
        cfg.print_cfg()
    if config.Ov:
        cfg.visualize()

    # Lokale Optimierungen auf Basisblöcken
    optimized_iir = []
    for x in cfg.part:
        y = cfg.last[cfg.part.index(x)]
        optimized_iir += constant_folding(cfg.iir[x : y + 1])

    cfg = CFGraph(optimized_iir)
    liveness(cfg)

    # Globale Optimierungen
    optimized_iir = spilling(cfg, config=config)
    # optimized_iir = dead_code_elimination(optimized_iir)

    # TODO: Weitere Optimierungen implementieren
    # optimized_iir = dead_code_elimination(optimized_iir)
    # optimized_iir = common_subexpression_elimination(optimized_iir)
    # optimized_iir = copy_propagation(optimized_iir)
    # optimized_iir = loop_invariant_code_motion(optimized_iir)
    # optimized_iir = strength_reduction(optimized_iir)

    print("Optimierung abgeschlossen.") if config.debug else None
    return optimized_iir


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
            if x is None or y is None:
                continue
            self.jump.setdefault(self.part.index(x + 1) - 1, []).append(
                self.part.index(y)
            )
        self.last = [x - 1 for x in self.part[1:]] + [len(iir) - 1]

    def print_cfg(self):
        """debuggind function to print the control flow graph and liveness info"""
        print("Control Flow Graph:")
        for i in range(len(self.part)):
            x, y = self.part[i], self.last[i]
            print(f"Block {i}: Instructions {x} to {y}")
            print("  Instructions:")
            for line in self.iir:
                print(
                    f"    {(str(line) + " " * 20)[:30]:30} {line.read=}, {line.write=}, {line.live_out=}"
                )
            print("  Jumps to:", self.jump.get(i, []))
        print()

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


class InterferenceGraph:
    def __init__(self, iir, exclude=None):
        self.nodes = set()
        self.edges = set()

        if exclude is None:
            exclude = set()

        # Sammle alle Register
        for inst in iir:
            self.nodes |= inst.live_in
            self.nodes |= inst.live_out
            self.nodes |= inst.read
            self.nodes |= inst.write

        def is_reg(r):
            if not isinstance(r, str) and not r.startswith("R"):
                return False
            if exclude and r in exclude:
                return False
            return True

        # Entferne spezielle Register und Nicht-Register
        self.nodes = {n for n in self.nodes if is_reg(n)}

        # Baue Interferenz-Kanten
        for inst in iir:
            live_regs = {r for r in inst.live_out if is_reg(r)}
            for r1 in inst.write:
                for r2 in live_regs:
                    if r1 != r2:
                        edge = tuple(sorted([r1, r2]))
                        self.edges.add(edge)
            live_list = sorted(live_regs)
            for i, r1 in enumerate(live_list):
                for r2 in live_list[i + 1 :]:
                    self.edges.add((r1, r2))

    def neighbors(self, node):
        """Gibt alle Nachbarn eines Knotens zurück"""
        n = set()
        for e1, e2 in self.edges:
            if e1 == node:
                n.add(e2)
            elif e2 == node:
                n.add(e1)
        return n

    def degree(self, node):
        """Gibt den Grad eines Knotens zurück"""
        return len(self.neighbors(node))

    def remove_node(self, node):
        """Entfernt einen Knoten aus dem Graph"""
        self.nodes.discard(node)
        self.edges = {(e1, e2) for e1, e2 in self.edges if e1 != node and e2 != node}

    def visualize(self, coloring=None, filename="dot/interference_graph"):
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
        for reg in sorted(self.nodes):
            if coloring and reg in coloring:
                color = cpal[coloring[reg] % len(cpal)]
            else:
                color = "#6c7086"
            dot.node(reg, reg, color=color)
        for x, y in self.edges:
            dot.edge(x, y, dir="none")

        dot.render(unique(filename), view=True)


def liveness(cfg):
    for i in range(len(iir := cfg.iir)):
        line = cfg.iir[i] = Inst(*iir[i])
        line.read = reads(line) - {"V"}
        line.write = writes(line) - {"V"}
        line.live_in = set()
        line.live_out = set()

    repeat = True
    while repeat:
        repeat = False
        for idx in reversed(range(len(iir))):
            inst = iir[idx]

            succ = []
            if hasattr(inst, "jump"):
                for src, dest in cfg.jump.items():
                    if idx in src:
                        for d in dest:
                            succ.append(iir[d])
            if idx + 1 < len(iir):
                succ = [iir[idx + 1]]
            old_live_in = inst.live_in.copy()
            old_live_out = inst.live_out.copy()
            inst.live_out = set()
            for s in succ:
                inst.live_out |= s.live_in
            inst.live_in = inst.read | (inst.live_out - inst.write)
            if inst.live_in != old_live_in or inst.live_out != old_live_out:
                repeat = True


# ------------ GRAPH COLORING ------------
def graph_coloring(graph, k):
    """
    Versucht den Interferenz-Graph mit k Farben zu färben.
    Gibt (erfolg, färbung, zu_spillende_knoten) zurück.
    """
    stack = []
    g = InterferenceGraph.__new__(InterferenceGraph)
    g.nodes = graph.nodes.copy()
    g.edges = graph.edges.copy()

    while g.nodes:
        # Finde Knoten mit Grad < k
        low_degree = [n for n in g.nodes if g.degree(n) < k]

        if low_degree:
            # Wähle einen Knoten mit niedrigem Grad
            node = low_degree[0]
            stack.append((node, False))
            g.remove_node(node)
        else:
            # Kein Knoten mit Grad < k gefunden -> Spilling notwendig
            if not g.nodes:
                break
            # Wähle Knoten zum Spillen (Heuristik: höchster Grad)
            node = max(g.nodes, key=lambda n: g.degree(n))
            stack.append((node, True))
            g.remove_node(node)

    coloring = {"R0": 0}
    to_spill = set()

    while stack:
        node, _ = stack.pop()

        # Finde verwendete Farben der Nachbarn
        neighbor_colors = {coloring[n] for n in graph.neighbors(node) if n in coloring}

        # Finde freie Farbe
        available_colors = set(range(k)) - neighbor_colors

        if available_colors:
            coloring[node] = min(available_colors)
        else:
            # Keine Farbe verfügbar -> muss gespillt werden
            to_spill.add(node)

    success = len(to_spill) == 0
    return success, coloring, to_spill


# ------------ SPILLING ------------
def insert_spill_code(iir, to_spill, spill_offset, RS, helper_regs):
    """
    Fügt Spill-Code für die angegebenen Register ein.
    Verwendet RS als Spill-Vektor und R_SPILL0-2 als Hilfsregister.
    """
    if not to_spill:
        return iir, spill_offset

    # Erstelle Mapping: Register -> Spill-Offset
    spill_map = spill_offset.copy()

    for reg in sorted(to_spill):
        if reg not in spill_map:
            spill_map[reg] = len(spill_map)

    # Durchlaufe alle Instruktionen und füge Spill-Code ein
    new_iir = []
    for inst in iir:
        reads_spilled = inst.read & to_spill
        writes_spilled = inst.write & to_spill

        helper_idx = 0
        helper_usage = []
        load_map = {}
        # Weise Hilfsregister zu
        for reg in reads_spilled | writes_spilled:
            if reg not in load_map:
                helper = helper_regs[helper_idx % len(helper_regs)]
                load_map[reg] = helper
                helper_usage.append(helper)
                helper_idx += 1

        # Lade gespillte Register vor der Instruktion
        for reg in reads_spilled:
            helper = load_map[reg]
            load_inst = Inst("=[]", "*", helper, RS, spill_map[reg])
            load_inst.read = {RS}
            load_inst.write = {helper}
            load_inst.live_out = inst.live_out.copy()
            new_iir.append(load_inst)

        # Ersetze gespillte Register in der Instruktion
        new_inst_tuple = tuple(load_map.get(x, x) for x in inst)
        new_inst = Inst(*new_inst_tuple)

        # Aktualisiere Metadaten
        new_inst.read = (inst.read - to_spill) | {
            load_map[r] for r in inst.read & to_spill
        }
        new_inst.write = (inst.write - to_spill) | {
            load_map[r] for r in inst.write & to_spill
        }
        new_inst.live_out = (inst.live_out - to_spill) | set(helper_usage)

        new_iir.append(new_inst)

        # Speichere gespillte Register nach der Instruktion
        for reg in writes_spilled:
            helper = load_map[reg]

            # Helper -> RS[offset]
            store_inst = Inst("[]=", RS, spill_map[reg], helper)
            store_inst.read = {RS, helper}
            store_inst.write = {RS}
            store_inst.live_out = inst.live_out.copy()
            new_iir.append(store_inst)

    return new_iir, spill_map


def spilling(cfg, max_registers=7, config={}):
    """
    Haupt-Spilling-Funktion mit iterativer Register-Allokation.

    Args:
        cfg: Control Flow Graph
        max_registers: Anzahl verfügbarer Register (k)

    Returns:
        Modifizierte Instruktionsliste
    """
    max_iterations = 20
    iteration = 0
    max_registers = max(max_registers, 7)

    RS = "RS"
    helper_regs = ["R_SPILL0", "R_SPILL1", "R_SPILL2"]
    exclude = {RS} | set(helper_regs)
    spill_map = {}
    spill_env_initialized = False

    while iteration < max_iterations:
        iteration += 1

        ig = InterferenceGraph(cfg.iir, exclude=exclude)

        success, coloring, to_spill = graph_coloring(
            ig, max_registers - len(helper_regs)
        )

        # Visualisiere Interferenz-Graph
        if config.Ov:
            ig.visualize(coloring)

        if success:
            # Erfolgreich gefärbt! Ersetze Register durch zugewiesene Register
            (
                print(f"Register-Allokation erfolgreich nach {iteration} Iteration(en)")
                if config.debug
                else None
            )
            print(f"Färbung: {coloring}") if config.debug else None

            ig = InterferenceGraph(cfg.iir, exclude={})
            _, coloring, _ = graph_coloring(ig, max_registers)

            # Erstelle Mapping
            reg_mapping = {old: f"R{color}" for old, color in coloring.items()}

            # Ersetze Register in allen Instruktionen
            # RS und Hilfsregister haben feste Zuordnung
            new_iir = []
            for inst in cfg.iir:
                new_inst = reassign_registers(inst, reg_mapping)
                new_iir.append(new_inst)

            return new_iir
        else:
            # Spilling notwendig
            (
                print(
                    f"Iteration {iteration}: Spilling von {len(to_spill)} Registern: {sorted(to_spill)}"
                )
                if config.debug
                else None
            )

            if not spill_env_initialized:
                labels_idxs = []

                for i, inst in enumerate(cfg.iir):
                    if inst[0] == "label" and (
                        inst[1] == "main" or inst[1].startswith("lambda_")
                    ):
                        labels_idxs.append(i)

                for idx_offset, main_idx in enumerate(labels_idxs):
                    alloc_inst = Inst("mk[]", "*", RS, 0)
                    alloc_inst.read = set()
                    alloc_inst.write = {RS}
                    alloc_inst.live_out = set()
                    insert_idx = main_idx + 1 + idx_offset
                    cfg.iir = cfg.iir[:insert_idx] + [alloc_inst] + cfg.iir[insert_idx:]
                spill_env_initialized = True

                liveness(cfg)

            # Füge Spill-Code ein
            cfg.iir, spill_map = insert_spill_code(
                cfg.iir, to_spill, spill_map, RS, helper_regs
            )

            num_spills = len(spill_map)
            for i, inst in enumerate(cfg.iir):
                if inst[0] == "mk[]" and len(inst) > 2 and inst[2] == RS:
                    new_inst = Inst("mk[]", "*", RS, num_spills)
                    new_inst.read = set()
                    new_inst.write = {RS}
                    new_inst.live_out = inst.live_out.copy()
                    cfg.iir[i] = new_inst

            # Aktualisiere Liveness-Analyse
            liveness(cfg)

    (
        print(
            f"Warnung: Register-Allokation nach {max_iterations} Iterationen nicht erfolgreich"
        )
        if config.debug
        else None
    )
    return cfg.iir


#  --------- CONSTANT FOLDING ---------
def constant_folding(iir):
    """
    Führt Constant Folding auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param iir: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit gefalteten Konstanten
    """
    optimized = []
    heap = {}

    def arg(a):
        return heap.get(a, a) if isinstance(a, str) and a.startswith("R") else a

    for instr in iir:
        match instr:
            case ("=", "R0", value) if isinstance(value, int):
                heap["R0"] = arg(value)
                optimized.append(instr)
            case ("=", tgt, value) if isinstance(value, int):
                heap[tgt] = value
            case "=[]", typ, res, vec, i:
                if i in heap:
                    optimized.append(("=[]", typ, res, vec, arg(i)))
                else:
                    optimized.append(instr)
                heap.pop(res, None)
            case "=[]", res, vec, i:
                if i in heap:
                    optimized.append(("=[]", res, vec, arg(i)))
                else:
                    optimized.append(instr)
                heap.pop(res, None)
            case "[]=", vec, i, val:
                optimized.append(("[]=", vec, i, arg(val)))
            case "get", res, _:
                optimized.append(instr)
                heap.pop(res, None)
            case ("mk[]", target, size):
                if size in heap:
                    optimized.append(("mk[]", target, arg(size)))
                    heap.pop(target, None)
                else:
                    optimized.append(instr)
                    heap.pop(target, None)
            case ("mk[]", ty, target, size):
                if size in heap:
                    optimized.append(("mk[]", ty, target, arg(size)))
                    heap.pop(target, None)
                else:
                    optimized.append(instr)
                    heap.pop(target, None)
            case (op, target, arg1, arg2) if op in {"+", "-", "*", "/", "%"}:
                val1 = arg(arg1)
                val2 = arg(arg2)
                if isinstance(val1, int) and isinstance(val2, int):
                    if op == "+":
                        result = val1 + val2
                    elif op == "-":
                        result = val1 - val2
                    elif op == "*":
                        result = val1 * val2
                    elif op == "/":
                        result = val1 // val2  # Ganzzahlige Division
                    elif op == "%":
                        result = val1 % val2  # Ganzzahlige Division
                    heap[target] = result
                    optimized.append(("=", target, result))
                elif isinstance(val1, int):
                    optimized.append((op, target, val1, arg2))
                    heap.pop(target, None)
                elif isinstance(val2, int):
                    optimized.append((op, target, arg1, val2))
                    heap.pop(target, None)
                else:
                    optimized.append(instr)
                    heap.pop(target, None)
            case (op, target, arg1, arg2) if op in {"<=", "<", ">=", ">", "==", "!="}:
                val1 = arg(arg1)
                val2 = arg(arg2)
                if isinstance(val1, int) and isinstance(val2, int):
                    if op == "<=":
                        result = int(val1 <= val2)
                    elif op == "<":
                        result = int(val1 < val2)
                    elif op == ">=":
                        result = int(val1 >= val2)
                    elif op == ">":
                        result = int(val1 > val2)
                    elif op == "==":
                        result = int(val1 == val2)
                    elif op == "!=":
                        result = int(val1 != val2)
                    heap[target] = result
                    optimized.append(("=", target, result))
                elif isinstance(val1, int):
                    optimized.append((op, target, val1, arg2))
                    heap.pop(target, None)
                elif isinstance(val2, int):
                    optimized.append((op, target, arg1, val2))
                    heap.pop(target, None)
                else:
                    optimized.append(instr)
                    heap.pop(target, None)
            case _:
                optimized.append(instr)

    return optimized


def dead_code_elimination(tac):
    """
    Führt Dead Code Elimination auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC ohne toten Code
    """
    optimized_tac = []
    live_vars = set()

    last_op = True
    for instruction in reversed(tac):
        match instruction:
            case ("=", "R0", _) if last_op:
                last_op = False
                optimized_tac.append(instruction)
            case ("=", target, _):
                if target in live_vars:
                    optimized_tac.append(instruction)
                    live_vars.discard(target)
            case _:
                optimized_tac.append(instruction)
                live_vars |= writes(instruction)

        live_vars -= writes(instruction)
        live_vars |= reads(instruction)

    optimized_tac.reverse()
    return optimized_tac


#  --------- COMMON SUBEXPRESSION ELIMINATION ---------
def common_subexpression_elimination(tac):
    """
    Führt Common Subexpression Elimination auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit eliminierten gemeinsamen Teilausdrücken
    """
    optimized_tac = []
    expr_map = {}

    for instruction in tac:
        match instruction:
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
                expr_key = (op, arg1, arg2)
                if expr_key in expr_map:
                    existing_target = expr_map[expr_key]
                    optimized_tac.append(("=", target, existing_target))
                else:
                    expr_map[expr_key] = target
                    optimized_tac.append(instruction)
            case _:
                optimized_tac.append(instruction)

    return optimized_tac


#  --------- COPY PROPAGATION ---------
def copy_propagation(iir):
    """
    Führt Copy Propagation auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit propagierten Kopien
    """
    pass
    cfg = CFGraph(iir)
    liveness(cfg)
    iir = cfg.iir
    for idx, inst in enumerate(iir):
        if inst[0] == "=":
            dest, src = inst[1], inst[2]

            for j in range(idx + 1, len(iir)):
                next_inst = iir[j]
                print(j, iir[j], next_inst.write)

                if dest in next_inst.write:
                    break

                next_inst.read = {src if r == dest else r for r in next_inst.read}

                next_inst_tuple = tuple(
                    src if operand == dest else operand for operand in next_inst
                )

                iir[j] = Inst(*next_inst_tuple)
    return iir


#  --------- DEAD CODE ELIMINATION ---------
def dead_code_elimination2(cfg):
    """
    Führt Dead Code Elimination auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param cfg: Control Flow Graph mit annotierten tac
    :return: Optimierter TAC ohne toten Code
    """
    iir = cfg.iir.copy()
    new_iir = []
    for inst in iir:
        if not inst.write:
            new_iir.append(inst)
        elif inst.write & inst.live_out:
            new_iir.append(inst)
        elif inst[0] in {"call", "ret", "ifgoto", "goto", "=[]", "[]=", "get", "mk[]"}:
            new_iir.append(inst)
        else:
            pass  # Tote Anweisung wird entfernt
    cfg = CFGraph(new_iir)
    liveness(cfg)
    if cfg.iir != iir:
        print("Dead Code Elimination: Entfernte Anweisungen")
    return cfg.iir


#  --------- LOOP INVARIANT CODE MOTION ---------
def loop_invariant_code_motion(tac):
    """
    Führt Loop Invariant Code Motion auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit verschobenem loop-invariantem Code
    """
    pass


#  --------- STRENGTH REDUCTION ---------
def strength_reduction(tac):
    """
    Führt Strength Reduction auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit reduzierter Rechenstärke
    """
    pass
