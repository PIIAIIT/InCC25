class Entry:
    value = None
    ty: str | None | tuple = None

    def __repr__(self):
        return "E:" + str(self.value)


class SymbolTable:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars: dict[str, Entry] = {}

    def push(self, names: list | tuple | set):
        """ """
        return SymbolTable(self).put(names)

    def put(self, names: list | tuple | set):
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

    def root(self):
        """Gibt das Oberste Environment aus! (Root)"""
        t = self
        while t.parent:
            t = t.parent
        return t

    def copy(self):
        """
        Erstellt eine neue copy des gleichen Environments.
        @return Seine eigene Kopie
        """
        new_env = SymbolTable(parent=self.parent)
        new_env.vars = self.vars.copy()
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

    def assign(self, name: list, value: list):
        """
        @arg name: Liste von pos, keyword und infty Argument (kein eval)
        @arg value: Liste von pos, keyword Argument (eval)
        @return void
        """
        # [('pos', 'x'), ('keyword', 'y', 3), ('keyword', 'z', 5), ('infty', 'c')]
        # Zuerst Keyword Args auf lambda env binden
        positional_args = [elem for elem in name if elem[0] == "pos"]
        keyword_args = [elem for elem in name if elem[0] == "keyword"]
        infty = name[-1][1] if name[-1][0] == "infty" else None

        call_positional, call_keywords = value

        for k, v in call_keywords.items():
            if k not in self:
                raise Exception("Invalid Argument Exception")
            self.define(k, v)

        # Dann Pos Args auf restliche lambda env binden
        all_param_names = positional_args + [elem[1] for elem in keyword_args]
        for key, val in zip(all_param_names, call_positional):
            self.define(key, val)

        if name[-1][0] == "infty":
            self.define(infty, call_positional[len(positional_args) :])

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
            "type": builtin_type,
            "assert": builtin_assert,
        }
        for name, fn in builtins.items():
            self.define(name, BuiltinFunction(name, fn))
            # self[name].value = BuiltinFunction(name, fn)

    def clear(self):
        self.parent = None
        self.vars = {}
        self.builtins()

    def __contains__(self, name):
        if name in self.vars:
            return True
        return self.parent and name in self.parent

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


class BuiltinFunction:
    def __init__(self, name, fn):
        self.fn = fn
        self.name = name

    def __call__(self, pos, key, eval):
        return self.fn(pos, key, eval)

    def __repr__(self):
        return f"<built-in {self.name}>"


def builtin_print(pos_args, key_args, _):
    """Ausgabe in der Kommandozeile"""
    print(*pos_args)
    return None


def builtin_len(pos_args, key_args, _):
    """Länge einer Liste/Array bestimmen"""
    # (1, (2, (3, None))) => 3
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
        return pos_args[0], None
    return (pos_args[0], builtin_list(pos_args[1:], None, _))


def builtin_type(pos_args, key_args, _):
    """Lisp Liste wird erstellt
    Example : list(1,2,3) == (1, (2, (3, None)))
            | list(1) == (1, None)
            | list() == (None)
    """
    return type(pos_args[0])


def builtin_assert(pos_args, key_args, _):
    """Assert a Statement
    assert(statement, erwartung)
    """
    statement = pos_args[0]
    erwartet = pos_args[1]
    assert statement == erwartet
    return int(statement == erwartet)
