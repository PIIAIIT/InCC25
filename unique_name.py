def generator():
    count = dict()

    def gen(name):
        nonlocal count
        if name not in count:
            count[name] = 0
        else:
            count[name] += 1
        return name + str(count[name])

    return gen
