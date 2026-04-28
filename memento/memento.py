
class Memento:
    def __init__(self, state):
        self.state = state

class Caretaker:
    def __init__(self):
        self.hist = []
    def save(self, state):
        self.hist.append(Memento(state))
    def undo(self):
        return self.hist.pop().state
