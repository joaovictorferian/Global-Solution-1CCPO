from Telemetry    import Telemetry
from Launch       import Launch
from Transit      import Transit
from Operation    import Operation
from Return       import Return
from EventEngine  import EventEngine
from CascadeFailure import CascadeFailure
from Dashboard import Dashboard

DESTINOS = {
    "1": ("LEO",   {"transito": 24,   "operacao": 48,   "retorno": 24}),
    "2": ("Lua",   {"transito": 72,   "operacao": 48,   "retorno": 72}),
    "3": ("Marte", {"transito": 5040, "operacao": 720,  "retorno": 5040}),
}

print("\n  Escolha o destino:")
print("  1 — LEO    (transito 24h | operação 48h  | retorno 24h)")
print("  2 — Lua    (transito 72h | operação 48h  | retorno 72h)")
print("  3 — Marte  (transito 5040h | operação 720h | retorno 5040h)")

escolha = input("\n  Digite o número: ").strip()
if escolha not in DESTINOS:
    print("Destino inválido.")
    exit()

nome, fases = DESTINOS[escolha]
print(f"\n  Destino: {nome}")

telemetry = Telemetry()

cascade = CascadeFailure()

dashboard = Dashboard()

tempo_acumulado = 0

engine_launch    = EventEngine(nome, "launch", cascade, )
launch    = Launch(telemetry, engine_launch, dashboard)
telemetry = launch.run()

tempo_acumulado += 5

engine_transit   = EventEngine(nome, "transit", cascade)
transit   = Transit(telemetry, fases["transito"], nome, engine_transit, dashboard)
telemetry = transit.run()

perfil_nave = transit.PERFIL_NAVE[nome]

engine_operation = EventEngine(nome, "operation", cascade)
operation = Operation(telemetry, fases["operacao"], nome, perfil_nave, engine_operation, dashboard)
telemetry = operation.run()

engine_return    = EventEngine(nome, "return", cascade)
retorno   = Return(telemetry, fases["retorno"], nome, perfil_nave, engine_return, dashboard)
telemetry = retorno.run()

if not telemetry.sucesso:
    telemetry.print_log()
    print("\n  Missão encerrada com falha!")
else:
    telemetry.print_log()
    print(f"\n{'═' * 70}")
    print(f"  MISSÃO CONCLUÍDA — {nome}")
    print(f"  Combustível restante : {telemetry.fuel:.1f}%")
    print(f"  Bateria              : {telemetry.battery:.1f}%")
    print(f"  Radiação acumulada   : {telemetry.radiation_exposure:.1f} mSv")
    print(f"  Status final         : {telemetry.status.upper()}")
    print(f"{'═' * 70}")

dashboard.exibir(nome)
