# adk/agent.py

class Agent:
    def __init__(self, name="Agent"):
        self.name = name

    def run(self, context):
        raise NotImplementedError("Subclasses must implement the run() method")
