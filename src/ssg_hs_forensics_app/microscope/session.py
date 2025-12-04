import datetime


class Session:
    """
    Tracks workflow steps, status, timestamps, errors, and networks.
    """

    def __init__(self):
        self.original_network = None
        self.status = "running"
        self.created = datetime.datetime.now().isoformat()
        self.steps = []
        self.error = None

    @classmethod
    def start_new(cls):
        return cls()

    def log_step(self, name, *data):
        self.steps.append({
            "step": name,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": data,
        })

    def fail(self, exc):
        self.status = "failed"
        self.error = str(exc)

    def complete(self):
        self.status = "success"
