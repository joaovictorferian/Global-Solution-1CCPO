class Telemetry:
    def __init__(self):
        self.fuel               = 0.0
        self.battery            = 0.0
        self.altitude           = 0.0
        self.signal             = 0.0
        self.structural_integrity = 0.0
        self.status             = "Normal"
        self.event_log          = []
        self.radiation_exposure = 0.0
        self.sucesso = True
        self.module_temp = 22.0

    def log(self, message):
        self.event_log.append(message)

    def print_log(self):
        print("=" * 70)
        print("\n  LOG DE EVENTOS: \n" )
        print("=" * 70)
        for entry in self.event_log:
            print(f"    → {entry}")