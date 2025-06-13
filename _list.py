
class Cons:
    def __init__(self, head, tail):
        self.head = head
        self.tail = tail

    def __iter__(self):
        current = self
        while isinstance(current, Cons):
            yield current.head
            current = current.tail
