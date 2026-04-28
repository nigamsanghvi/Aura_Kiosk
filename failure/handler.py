
class Handler:
    def __init__(self, nxt=None):
        self.next = nxt
    def handle(self, issue):
        return self.next.handle(issue) if self.next else "Unhandled"

class Retry(Handler):
    def handle(self, issue):
        if issue=="temporary": return "Retry success"
        return super().handle(issue)

class Alert(Handler):
    def handle(self, issue):
        return "Alert sent"
