from ice_machine import run, tac_tupel_to_infix


def print_instructions(instructions):
    for pc, inst in enumerate(instructions):
        print(pc, ":\t", tac_tupel_to_infix(inst))
    res = run(instructions)
    print("Result:", res["R0"])


def aufgabe_1():
    instructions = [
        ("label", "main"),
        ("=", "R0", 42),
    ]
    print_instructions(instructions)


def aufgabe_2():
    instructions = [("label", "main"), ("*", "R0", 21, 2)]
    print_instructions(instructions)


def aufgabe_3():
    instructions = [
        ("label", "main"),
        ("+", "R0", 3, 4),
        ("/", "R0", 7, 3),
        ("=", "R0", 42),
    ]
    print_instructions(instructions)


def aufgabe_4():
    instructions = [
        ("label", "main"),
        ("+", "R0", 3, 4),
        ("*", "R1", 24, 2),
        ("*", "R0", "R0", 5),
        ("+", "R0", "R0", 3),
        ("-", "R1", "R1", 1),
        ("+", "R0", "R0", "R1"),
        ("/", "R0", "R0", 2),
    ]
    print_instructions(instructions)


def aufgabe_5():
    instructions = [
        ("label", "main"),
        ("==", "R1", 1, 2),
        ("ifgoto", "R1", "then"),
        ("=", "R0", 42),
        ("goto", "if_end"),
        ("label", "then"),
        ("=", "R0", 41),
        ("label", "if_end"),
    ]
    print_instructions(instructions)


if __name__ == "__main__":
    print("Aufgabe 1:")
    aufgabe_1()
    print("\nAufgabe 2:")
    aufgabe_2()
    print("\nAufgabe 3:")
    aufgabe_3()
    print("\nAufgabe 4:")
    aufgabe_4()
    print("\nAufgabe 5:")
    aufgabe_5()
