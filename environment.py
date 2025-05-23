class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}

    def put(self, names: list | tuple):
        for name in names:
            if name not in self.vars:
                self.vars[name] = None
        return self

    def copy(self):
        new_env = Environment(parent=self.parent)
        new_env.vars = self.vars.copy()
        return new_env

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
        lines = []
        env = self
        level = 0
        while env is not None:
            indent = "  " * level
            scope_type = "Global" if env.parent is None else f"Scope Level {level}"
            lines.append(f"{indent}{scope_type}: {env.vars}")
            env = env.parent
            level += 1
        return "\n".join(reversed(lines))
