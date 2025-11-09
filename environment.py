# ------------------- Environment -------------------#
class Entry:
    def __init__(self):
        self.value: None
        self.idx: int
        self.ty: str

    def __repr__(self):
        return (
            f"<Entry value={self.value}>"
            if hasattr(self, "value")
            else f"<Entry type={self.ty}>"
        )


class SymbolTable:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars: dict[str, Entry] = {}

    def push(self, names: list | str):
        """
        Erstellt ein neues Environment mit dem aktuellen als Parent.
        @arg names: Kann eine Liste oder Tuple sein
        @return gibt das neue Environment als Object aus
        """
        return SymbolTable(self).put(names)

    def put(self, names):
        """
        Packt Jedes Element der Liste als undefiniert auf dem Environment.
        @arg names: Kann eine Liste oder Tuple sein
        @return gibt sich selber als Object aus
        """
        if not isinstance(names, (list, tuple, set)):
            names = [names]
        for name in names:
            if name not in self.vars:
                self.vars[name] = Entry()
        return self

    def copy(self, item=None):
        """
        Erstellt eine neue copy des gleichen Environments.
        @return Seine eigene Kopie
        """
        new_env = SymbolTable(parent=self.parent)
        new_env.vars = self.vars.copy()
        if item:
            self.put(item)
        return new_env

    def define(self, name, value):
        """
        Definiert eine Variablen auf dem Environment.
        @arg name: Name der Variable
        @arg value: Wert der Variable
        """
        self.put(name)
        self[name].value = value
        return self

    def builtins(self):
        """
        Definiert eine Variablen auf dem Environment.
        @arg name: Name der Variable
        @arg value: Wert der Variable
        """
        builtins = {
            "echo": builtin_print,
            "länge": builtin_len,
            "list": builtin_list,
            "assert": builtin_assert,
        }
        for name, fn in builtins.items():
            self.define(name, BuiltinFunction(name, fn))

    def clear(self):
        self.parent = None
        self.vars = {}
        self.builtins()

    def __contains__(self, name):
        if name in self.vars:
            return True
        return self.parent and name in self.parent

    def __getitem__(self, name) -> Entry:
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
            raise KeyError(name)
        else:
            self.parent[name] = value

    def __delitem__(self, name):
        if name in self.vars:
            del self.vars[name]
        elif self.parent is None:
            raise KeyError(name)
        else:
            del self.parent[name]

    def __str__(self):
        s = str(self.vars)
        if self.parent:
            s += "\n" + str(self.parent)
        return s


# ------------------- Builtin Function -------------------#
class BuiltinFunction:
    def __init__(self, name, fn):
        self.name = name
        self.fn = fn

    def __call__(self, pos, key, eval):
        return self.fn(pos, key, eval)

    def __repr__(self):
        return f"<built-in {self.name}>"


def builtin_print(pos_args, key_args, _):
    """
    Gibt die Argumente auf der Konsole aus
    Example : echo(1,2,3) -> 1 2 3
    """
    print(*pos_args, **key_args)
    return None


def builtin_len(pos_args, key_args, _):
    """
    Länge einer Liste wird zurückgegeben
    Example : len((1, (2, (3, None)))) == 3
    """
    if isinstance(pos_args[0], tuple):
        list_len = lambda lst: 1 if lst[1] is None else 1 + list_len(lst[1])
        return list_len(pos_args[0])
    return len(pos_args[0])


def builtin_list(pos_args, key_args, _):
    """Lisp Liste wird erstellt
    Example : list(1,2,3) == (1, (2, (3, None)))
            | list(1) == (1, None)
            | list() == (None)
    """
    if len(pos_args) == 0:
        return None
    if len(pos_args) == 1:
        return (pos_args[0], None)
    return (pos_args[0], builtin_list(pos_args[1:], None, _))


def builtin_assert(pos_args, key_args, _):
    """Assert a Statement
    assert(statement, erwartung)
    """
    statement = pos_args[0]
    erwartet = pos_args[1]
    assert statement == erwartet
    return int(statement == erwartet)
