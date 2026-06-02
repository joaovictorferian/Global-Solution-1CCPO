import random

class Transit:

    MAGNETOSFERA = 60000.0

    def __init__(self, telemetry, duration):
        self.telemetry         = telemetry
        self.duration          = duration
        self.tick              = 0
        self.distance_traveled = 0.0

        if duration > 200:
            self.horas_por_tick    = 10
            self.intervalo_print   = 100
        else:
            self.horas_por_tick    = 1
            self.intervalo_print   = 1

        self.total_ticks = duration // self.horas_por_tick

    # ─── loop principal ──────────────────────────────

    def run(self):
        print("\n" + "═" * 60)
        print("  FASE 2 — TRÂNSITO")
        print(f"  Duração: {self.duration}h | "
              f"1 tick = {self.horas_por_tick}h | "
              f"Total: {self.total_ticks} ticks")
        print("═" * 60)

        while self.tick < self.total_ticks:
            self._update()
            alertas_novos = self._check_alerts()
            self._print_status(forcar=alertas_novos)
            self.tick += 1

            if self.telemetry.status == "critical":
                print("\n  ✖ Situação crítica durante o trânsito.")
                break

        print("\n  Trânsito concluído.")
        return self.telemetry

    # ─── atualiza os valores a cada tick ─────────────

    def _update(self):
        t  = self.telemetry
        dt = self.horas_por_tick

        self.distance_traveled += 50.0 * dt

        # — geração solar variável —
        fator_solar = max(0.70, 1.0 - (self.distance_traveled / 800000.0))
        geracao = 80.0 * fator_solar * random.uniform(0.85, 1.15)

        # — consumo variável —
        consumo = 55.0 * random.uniform(0.90, 1.20)

        # — saldo de energia (escalado pelo dt) —
        saldo     = geracao - consumo
        t.battery += saldo * 0.05 * dt
        t.battery  = max(0.0, min(100.0, t.battery))

        # — sinal —
        sinal_base = max(5.0, 100.0 - (self.distance_traveled / 150.0))
        t.signal   = max(5.0, min(100.0, sinal_base + random.uniform(-3.0, 3.0)))

        # — radiação escalada pelo dt —
        if self.distance_traveled < self.MAGNETOSFERA:
            rad_hora = 0.3 + 0.3 * (self.distance_traveled / self.MAGNETOSFERA)
        else:
            excesso  = self.distance_traveled - self.MAGNETOSFERA
            rad_hora = 0.6 + (excesso / 200000.0)
            rad_hora = min(rad_hora, 4.0)

        rad_hora *= random.uniform(0.80, 1.30)
        t.radiation_exposure = getattr(t, 'radiation_exposure', 0.0)
        t.radiation_exposure += rad_hora * dt

    # ─── verifica alertas, retorna True se algo novo disparou ────

    def _check_alerts(self):
        t      = self.telemetry
        novo   = False
        tempo  = self.tick * self.horas_por_tick

        if t.battery <= 10.0:
            t.status = "critical"
            t.log(f"[T+{tempo}h] CRÍTICO — Bateria em colapso: {t.battery:.1f}%")
            novo = True

        elif t.battery <= 30.0:
            if t.status == "nominal":
                t.status = "warning"
                t.log(f"[T+{tempo}h] AVISO — Bateria baixa: {t.battery:.1f}%")
                novo = True

        if t.signal <= 30.0:
            if t.status == "nominal":
                t.status = "warning"
                t.log(f"[T+{tempo}h] AVISO — Sinal fraco: {t.signal:.1f}%")
                novo = True

        if t.radiation_exposure >= 200.0:
            if t.status == "nominal":
                t.status = "warning"
                t.log(f"[T+{tempo}h] AVISO — Radiação alta: {t.radiation_exposure:.1f} mSv")
                novo = True

        return novo

    # ─── imprime conforme intervalo ou alerta ────────

    def _print_status(self, forcar=False):
        if not forcar and (self.tick % self.intervalo_print != 0):
            return

        t    = self.telemetry
        rad  = getattr(t, 'radiation_exposure', 0.0)
        tempo = self.tick * self.horas_por_tick
        icons = {"nominal": "✓", "warning": "⚠", "critical": "✖"}
        icon  = icons.get(t.status, "?")

        print(
            f"  T+{tempo:6.0f}h {icon} | "
            f"Dist: {self.distance_traveled:8.0f}km | "
            f"Bat: {t.battery:5.1f}% | "
            f"Sinal: {t.signal:5.1f}% | "
            f"Rad: {rad:7.1f}mSv"
        )