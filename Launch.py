import time
import threading
from playsound import playsound

class Launch:

    TICKS_DECOLAGEM = 2
    TICKS_SUBIDA    = 3
    contagem = 10

    def __init__(self, telemetry, event_engine,callbacks=None):
        self.callbacks = callbacks or {}
        self.telemetry = telemetry
        self.event_engine = event_engine
        self.tickNow = 0
        self.phase  = "Decolagem"

        self.telemetry.fuel = 100.0
        self.telemetry.battery = 100.0
        self.telemetry.altitude = 0.0
        self.telemetry.signal = 100.0
        self.telemetry.structural_integrity = 100.0
        self.telemetry.status = "nominal"

    # ─── loop principal ──────────────────────────────

    def run(self):
        print("\n" + "═" * 50)
        print("  FASE 1 — LANÇAMENTO")
        print("═" * 50)

        if self.callbacks.get("emitir_audio"):
            self.callbacks["emitir_audio"]("decolagem")
            
        while self.contagem > 0:
            print(f"Iniciando lançamento em: {self.contagem}")
            if self.callbacks.get("emitir_contagem"):
                self.callbacks["emitir_contagem"](self.contagem)
            time.sleep(1)
            self.contagem -= 1

        if self.callbacks.get("emitir_contagem"):
            self.callbacks["emitir_contagem"](0)

        time.sleep(9)


        total_ticks = self.TICKS_DECOLAGEM + self.TICKS_SUBIDA

        while self.tickNow < total_ticks:
            if self.tickNow < self.TICKS_DECOLAGEM:
                self.phase = "decolagem"
            else:
                self.phase = "subida"

            self._update()
            self.event_engine.sortear_evento(self.telemetry, self.tickNow)
            self.event_engine.processar_eventos_ativos(self.telemetry, self.tickNow)
            self._check_alerts()
            self._print_status()

            if self.callbacks.get("emitir_telemetria"):
                self.callbacks["emitir_telemetria"](
                    self.telemetry, "launch", self.tickNow, 1,
                    {}
                )

            self.tickNow += 1

        print("\n  Órbita atingida. Lançamento concluído.")
        return self.telemetry

    def _update(self):
        telemetry = self.telemetry

        if self.phase == "Decolagem":
            telemetry.fuel      -= 10.0
            telemetry.battery   -= 8.0
            telemetry.altitude  += 40.0
            telemetry.signal    -= 15.0
            telemetry.module_temp += 15.0

        elif self.phase == "Subida":
            telemetry.fuel      -= 5.0
            telemetry.battery   -= 3.0
            telemetry.altitude  += 160.0
            telemetry.signal    += 5.0
            telemetry.module_temp -= 5.0

        # garante que nenhum valor passa dos limites possíveis
        telemetry.fuel    = max(0.0, min(100.0, telemetry.fuel))
        telemetry.battery = max(0.0, min(100.0, telemetry.battery))
        telemetry.signal  = max(0.0, min(100.0, telemetry.signal))

    # ─── verifica alertas depois de cada update ──────

    def _check_alerts(self):
        telemetry = self.telemetry

        if telemetry.fuel <= 0:
            telemetry.status = "critical"
            telemetry.log(f"[T+ {self.tickNow}] CRÍTICO — Combustível esgotado antes de atingir órbita")

        elif telemetry.fuel <= 10:
            telemetry.status = "critical"
            telemetry.log(f"[T+ {self.tickNow}] CRÍTICO — Nível de combustível EXTREMAMENTE BAIXO antes de atingir órbita")

        elif telemetry.fuel <= 60:
            if telemetry.status == "nominal":
                telemetry.status = "warning"
            telemetry.log(f"[T+ {self.tickNow}] AVISO — Combustível baixo: {telemetry.fuel:.1f}%")

        if telemetry.battery <= 30:
            telemetry.status = "critical"
            telemetry.log(f"[T+ {self.tickNow}] CRÍTICO — Nível da bateria baixo: {telemetry.battery:.1f}%")

        elif telemetry.battery <= 70:
            if telemetry.status == "nominal":
                telemetry.status = "warning"
            telemetry.log(f"[T+ {self.tickNow}] AVISO — Nível da bateria relativamente baixo: {telemetry.battery:.1f}%")

        if telemetry.structural_integrity <= 80:
            telemetry.status = "critical"
            telemetry.log(f"[T+ {self.tickNow}] CRÍTICO — Falha estrutural: {telemetry.structural_integrity:.1f}%")

        if telemetry.module_temp >= 80.0:
            telemetry.status = "critical"
            telemetry.log(f"[T+{self.tickNow}h] CRÍTICO — Superaquecimento dos módulos: {telemetry.module_temp:.1f}°C")
            novo = True
        elif telemetry.module_temp <= -100.0:
            telemetry.status = "critical"
            telemetry.log(f"[T+{self.tickNow}h] CRÍTICO — Congelamento dos módulos: {telemetry.module_temp:.1f}°C")
            novo = True
        elif telemetry.module_temp >= 60.0 or telemetry.module_temp <= -60.0:
            if telemetry.status == "nominal":
                telemetry.status = "warning"
                telemetry.log(f"[T+{self.tickNow}h] AVISO — Temperatura dos módulos: {telemetry.module_temp:.1f}°C")
                novo = True

    # ─── imprime o estado do tickNow atual ──────────────

    def _print_status(self):
        telemetry = self.telemetry
        icons = {"nominal": "✓", "warning": "⚠", "critical": "✖"}
        icon  = icons.get(telemetry.status, "?")

        print(
            f"  tickNow {self.tickNow + 1} [{self.phase:9s}] {icon} | "
            f"Alt: {telemetry.altitude:5.0f}km | "
            f"Comb: {telemetry.fuel:5.1f}% | "
            f"Bat: {telemetry.battery:5.1f}% | "
            f"Sinal: {telemetry.signal:5.1f}%"
            f"Temp: {telemetry.module_temp:5.1f}°C"
        )
