class Telemetry:
    def __init__(self):
        self.fuel               = 0.0
        self.battery            = 0.0
        self.altitude           = 0.0
        self.signal             = 0.0
        self.structural_integrity = 0.0
        self.status             = "Normal"
        self.event_log          = []

    def log(self, message):
        self.event_log.append(message)

    def print_log(self):
        print("\n  LOG DE EVENTOS:")
        for entry in self.event_log:
            print(f"    → {entry}")