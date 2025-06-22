def builtin_print(pos_args, key_args):
    """Ausgabe in der Kommandozeile"""
    print(*pos_args)
    return None


def builtin_len(pos_args, key_args):
    """Länge einer Liste/Array bestimmen"""
    return len(pos_args[0])


def builtin_list(pos_args, key_args):
    """Lisp Liste wird erstellt
    Example : list(1,2,3) == (1, (2, (3, None)))
            | list(1) == (1, None)
            | list() == (None)
    """
    if len(pos_args) == 0:
        return (None,)
    if len(pos_args) == 1:
        return pos_args[0], None
    return (pos_args[0], builtin_list(pos_args[1:], None))


class BuiltinFunction:
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, pos, key):
        return self.fn(pos, key)
