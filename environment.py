class Environment(dict):
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}

    def put(self, names: list | tuple | set):
        """
        Packt Jedes Element der Liste als undefiniert auf dem Environment.
        @arg names: Kann eine Liste oder Tuple sein
        @return gibt sich selber als Object aus
        """
        for name in names:
            if name not in self.vars:
                self.vars[name] = None
        return self

    def copy(self):
        """
        Erstellt eine neue copy des selben Environments.
        @return Seine eigene Kopie
        """
        new_env = Environment(parent=self.parent)
        new_env.vars = self.vars.copy()
        return new_env

    def define(self, name, value):
        """
        Definiert eine Variablen auf dem Environment.
        @arg name: Name der Variable
        @arg value: Wert der Variable
        """
        assert name is not None
        assert value is not None
        self.__setitem__(name, value)

    def builtins(self):
        """
        Definiert eine Variablen auf dem Environment.
        @arg name: Name der Variable
        @arg value: Wert der Variable
        """
        builtins = {
            "echo": BuiltinFunction(builtin_print),
            "länge": BuiltinFunction(builtin_len),
            "list": BuiltinFunction(builtin_list),
            "type": BuiltinFunction(builtin_type)
        }

        for name, fn in builtins.items():
            self[name] = fn

    def __contains__(self, name):
        if name in self.vars:
            return True
        elif self.parent is None:
            return False
        else:
            return name in self.parent

    def __getitem__(self, name):
        if name in self.vars:
            return self.vars[name]
        elif self.parent is None:
            raise KeyError(name)
        else:
            return self.parent[name]

    def __setitem__(self, name, value):
        if name in self.vars:
            self.vars[name] = value
        elif self.parent is None:
            self.vars[name] = value
        else:
            self.parent[name] = value

    def __str__(self):
        return str(self.vars) + "\n" + str(self.parent) if self.parent is not None else ""


class BuiltinFunction:
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, pos, key):
        return self.fn(pos, key)


def builtin_print(pos_args, key_args):
    """Ausgabe in der Kommandozeile"""
    print(*pos_args)
    return None


def builtin_len(pos_args, key_args):
    """Länge einer Liste/Array bestimmen"""
    # (1, (2, (3, None))) => 3
    if isinstance(pos_args[0], tuple):
        list_len = lambda lst : 1 if lst[1] is None else 1 + list_len(lst[1])
        return list_len(pos_args[0])
    return len(pos_args[0])


def builtin_list(pos_args, key_args):
    """Lisp Liste wird erstellt
    Example : list(1,2,3) == (1, (2, (3, None)))
            | list(1) == (1, None)
            | list() == (None)
    """
    if len(pos_args) == 0:
        return None
    if len(pos_args) == 1:
        return pos_args[0], None
    return (pos_args[0], builtin_list(pos_args[1:], None))


def builtin_type(pos_args, key_args):
    """Lisp Liste wird erstellt
    Example : list(1,2,3) == (1, (2, (3, None)))
            | list(1) == (1, None)
            | list() == (None)
    """
    return type(pos_args[0])
