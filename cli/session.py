class GandalfSession:
    """
    Manages the session state for the Gandalf CLI.
    Currently a skeleton for future state management.
    """
    def __init__(self):
        self.context = {}

    def update_context(self, key, value):
        self.context[key] = value

    def get_context(self, key, default=None):
        return self.context.get(key, default)
