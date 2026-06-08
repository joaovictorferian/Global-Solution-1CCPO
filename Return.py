import random
import math
import time
from MissionReport import MissionReport

class Return:
    distanciaSolTerra = 150_000_000.0
    distanciaSolMarte = 228_000_000.0
    irrandianciaSolTerra = 1368.0
    magnetosfera = 60_000.0
    capacidadeBateria_KWH = 200.0
    distanciaParaAtivacaoNuclear = 152_000_000

    TEMP_CASCO_WARNING = 800.0
    TEMP_CASCO_CRITICAL = 1200.0

    def __init__(self, telemetry, duration, destino, perfil_nave, event_engine, callbacks=None):
        self.callbacks = callbacks or {}
        self.telemetry = telemetry
        self.event_engine = event_engine
        self.duration = duration
        self.destino = destino
        self.tick = 0
        self.geracao_solar_kw = perfil_nave["geracao_solar_kw"]
        self.consumo_base_kw = perfil_nave["consumo_base_kw"]
        self.consumo_comms_kw = perfil_nave["consumo_comms_kw"]
        self.geracao_nuclear_kw = perfil_nave["geracao_nuclear_kw"]
        self.nuclear_ativa = self.geracao_nuclear_kw > 0
        self.distancia_total = perfil_nave["distancia_km"]
        self.frequencia_mhz = perfil_nave["frequencia_mhz"]
        self.potencia_tx_dbm = perfil_nave["potencia_tx_dbm"]
        self.rx_warning_dbm = perfil_nave["rx_warning_dbm"]
        self.rx_critical_dbm = perfil_nave["rx_critical_dbm"]
        self.velocidade_kmh = self.distancia_total / duration

        match self.destino:
            case "Marte":
                self.intervalo = 10
                self.intervalo_ciclo = 20
            case "LEO":
                self.intervalo = 10
                self.intervalo_ciclo = 8

            case "Lua":
                self.intervalo = 20
                self.intervalo_ciclo = 12

        self.distance_remaining = float(self.distancia_total)

        if duration > 1000:
            self.horas_por_tick = 50
            self.intervalo_print = 20
        elif duration > 200:
            self.horas_por_tick = 10
            self.intervalo_print = 100
        else:
            self.horas_por_tick = 1
            self.intervalo_print = 1

        self.total_ticks = duration // self.horas_por_tick

        if self.telemetry.status != "nominal":
            self.telemetry.status = "nominal"
        self._fator_solar_atual = 0.43
        self._potencia_rx_atual = 0.0
        self._hull_temp = 20.0

        self._check_alerts()

    # FSPL = Free Space Path Loss - Fórmula responsável por calcular a perda de força do sinal de rádio no espaço profundo.
    def _fspl(self, distancia_km):
        if distancia_km <= 0:
            distancia_km = 1.0
        return (20 * math.log10(distancia_km)
                + 20 * math.log10(self.frequencia_mhz)
                + 32.44)

    def _potencia_rx(self, distancia_km):
        perda = self._fspl(distancia_km)
        ruido = random.uniform(-1.5, 1.5)
        return self.potencia_tx_dbm - perda + ruido

    def _fator_solar(self):
        if self.destino != "Marte":
            return 1.0
        progresso = min(1.0, 1.0 - (self.distance_remaining / self.distancia_total))
        distanciaSolAtual = (self.distanciaSolMarte
                       - progresso * (self.distanciaSolMarte - self.distanciaSolTerra))
        distanciaSolAtual = max(self.distanciaSolTerra, distanciaSolAtual)
        return (self.distanciaSolTerra / distanciaSolAtual) ** 2


    def run(self):
        print("\n" + "═" * 70)
        print("  FASE 4 — RETORNO")
        print(f"  Origem   : {self.destino} → Terra")
        print(f"  Duração  : {self.duration}h | "
              f"1 tick = {self.horas_por_tick}h | "
              f"Total: {self.total_ticks} ticks")
        print("═" * 70)

        while self.tick < self.total_ticks:
            self._update()
            self.event_engine.sortear_evento(self.telemetry, self.tick)
            self.event_engine.processar_eventos_ativos(self.telemetry, self.tick)
            alertas_novos = self._check_alerts()

            if self.tick % self.intervalo == 00 and self.tick > 0:
                time.sleep(5)

            self._print_status(forcar=alertas_novos)

            if self.callbacks.get("emitir_telemetria"):
                self.callbacks["emitir_telemetria"](
                    self.telemetry, "transit", self.tick, self.horas_por_tick,
                    {
                        "fator_solar": self._fator_solar_atual,
                        "nuclear_ativa": self.nuclear_ativa,
                        "geracao_solar_kw": round(self._geracao_solar_atual, 1),
                        "geracao_nuclear_kw": round(self._geracao_nuclear_atual, 0),
                        "geracao_total_kw": round(self._geracao_total_atual, 1),
                        "consumo_total_kw": round(self._consumo_total_atual, 1),
                    }
                )

                if self.tick % self.intervalo_ciclo == 0 and self.tick > 0:
                    if self.callbacks.get("registrar_ciclo"):
                        signal_pct = MissionReport.sinal_para_percentual(
                            self.telemetry.signal,
                            self.rx_warning_dbm,
                            self.rx_critical_dbm,
                        )
                        self.callbacks["registrar_ciclo"](self.telemetry, signal_pct)

            self.tick += 1

            if self.telemetry.status == "critical":
                print("\n  ✖ Situação crítica durante o retorno.")

            if self.telemetry.battery == 0.0:
                print("  ✖ Bateria em estado crítico! Impossível prosseguir com a missão...")
                self.telemetry.sucesso = False
                return self.telemetry
            elif self.telemetry.fuel == 0.0:
                print("  ✖ Combustível insuficiente para manobra! Impossível prosseguir com a missão...")
                self.telemetry.sucesso = False
                return self.telemetry

        print("\n  Retorno concluído. Nave em aproximação à Terra.")
        return self.telemetry

    def _update(self):
        t = self.telemetry
        dt = self.horas_por_tick

        self.distance_remaining = max(0.0, self.distance_remaining - self.velocidade_kmh * dt)

        fator = self._fator_solar()
        self._fator_solar_atual = fator
        geracao_solar_kw = self.geracao_solar_kw * fator * random.uniform(0.85, 1.15)

        distancia_do_sol = self.distanciaSolTerra + self.distance_remaining

        nuclear_desativada = False
        for evento_ativo in self.event_engine.eventos_ativos:
            if evento_ativo["evento"].get("desativa_nuclear", False):
                nuclear_desativada = True
                break

        if self.geracao_nuclear_kw > 0 and distancia_do_sol >= self.distanciaParaAtivacaoNuclear and not nuclear_desativada:
            geracao_nuclear_kw = self.geracao_nuclear_kw * random.uniform(0.95, 1.05)
            self.nuclear_ativa = True
        else:
            geracao_nuclear_kw = 0.0
            self.nuclear_ativa = False

        geracao_total_kw = geracao_solar_kw + geracao_nuclear_kw

        dist_atual = max(400.0, self.distance_remaining)
        self._potencia_rx_atual = self._potencia_rx(dist_atual)
        t.signal = self._potencia_rx_atual

        consumo_base_kw = self.consumo_base_kw * random.uniform(0.90, 1.10)
        consumo_total_kw = consumo_base_kw + self.consumo_comms_kw

        temp_solar = 30.0 * self._fator_solar_atual
        temp_consumo = 10.0 * (consumo_base_kw / 4.0)
        temp_base = -40.0
        temp_alvo = temp_base + temp_solar + temp_consumo
        t.module_temp += (temp_alvo - t.module_temp) * 0.01 * dt

        saldo_kw = geracao_total_kw - consumo_total_kw
        variacao_pct = (saldo_kw * dt / self.capacidadeBateria_KWH) * 100
        t.battery += variacao_pct
        t.battery = max(0.0, min(100.0, t.battery))

        self._geracao_solar_atual = geracao_solar_kw
        self._geracao_nuclear_atual = geracao_nuclear_kw
        self._consumo_total_atual = consumo_total_kw
        self._geracao_total_atual = geracao_solar_kw + geracao_nuclear_kw

        if self.tick < 3:
            t.fuel -= 4.0
        else:
            t.fuel -= 0.005 * dt

        t.fuel = max(0.0, t.fuel)

        if self.distance_remaining > self.magnetosfera:
            excesso = self.distance_remaining - self.magnetosfera
            rad_hora = 0.6 + (excesso / 200_000.0)
            rad_hora = min(rad_hora, 4.0)
        else:
            rad_hora = 0.1
        rad_hora *= random.uniform(0.80, 1.30)
        t.radiation_exposure += rad_hora * dt

        ticks_restantes = self.total_ticks - self.tick
        if ticks_restantes <= 3:
            self._hull_temp += 300.0 * dt * random.uniform(0.9, 1.1)
            t.module_temp += 300.0 * dt * random.uniform(0.9, 1.1)
        else:
            self._hull_temp = max(20.0, self._hull_temp - 5.0 * dt)
            t.module_temp = max(20.0, t.module_temp - 5.0 * dt)


    def _check_alerts(self):
        t = self.telemetry
        novo = False
        tempo = self.tick * self.horas_por_tick
        rx = self._potencia_rx_atual

        if t.battery <= 10.0:
            t.status = "critical"
            t.log(f"[T+{tempo}h] CRÍTICO — Bateria em colapso: {t.battery:.1f}%")
            novo = True
        elif t.battery <= 30.0:
            if t.status == "nominal":
                t.status = "warning"
                t.log(f"[T+{tempo}h] AVISO — Bateria baixa: {t.battery:.1f}%")
                novo = True

        if rx <= self.rx_critical_dbm:
            t.status = "critical"
            t.log(f"[T+{tempo}h] CRÍTICO — Sinal perdido: {rx:.1f} dBm")
            novo = True
        elif rx <= self.rx_warning_dbm:
            if t.status == "nominal":
                t.status = "warning"
                t.log(f"[T+{tempo}h] AVISO — Sinal fraco: {rx:.1f} dBm")
                novo = True

        if t.fuel <= 5.0:
            t.status = "critical"
            t.log(f"[T+{tempo}h] CRÍTICO — Combustível insuficiente para manobra: {t.fuel:.1f}%")
            novo = True

        if self._hull_temp >= self.TEMP_CASCO_CRITICAL:
            t.status = "critical"
            t.log(f"[T+{tempo}h] CRÍTICO — Temperatura do casco: {self._hull_temp:.0f}°C")
            novo = True
        elif self._hull_temp >= self.TEMP_CASCO_WARNING:
            if t.status == "nominal":
                t.status = "warning"
                t.log(f"[T+{tempo}h] AVISO — Temperatura de reentrada: {self._hull_temp:.0f}°C")
                novo = True

        if t.module_temp >= 80.0:
            t.status = "critical"
            t.log(f"[T+{tempo}h] CRÍTICO — Superaquecimento dos módulos: {t.module_temp:.1f}°C")
            novo = True
        elif t.module_temp <= -100.0:
            t.status = "critical"
            t.log(f"[T+{tempo}h] CRÍTICO — Congelamento dos módulos: {t.module_temp:.1f}°C")
            novo = True
        elif t.module_temp >= 60.0 or t.module_temp <= -60.0:
            if t.status == "nominal":
                t.status = "warning"
                t.log(f"[T+{tempo}h] AVISO — Temperatura dos módulos: {t.module_temp:.1f}°C")
                novo = True

        return novo

    def _print_status(self, forcar=False):
        if not forcar and (self.tick % self.intervalo_print != 0):
            return

        t = self.telemetry
        rad = t.radiation_exposure
        tempo = self.tick * self.horas_por_tick
        icons = {"nominal": "✓", "warning": "⚠", "critical": "✖"}
        icon = icons.get(t.status, "?")

        print(
            f"  T+{tempo:6.0f}h {icon} | "
            f"Solar: {self._fator_solar_atual * 100:4.0f}% | "
            f"Bat: {t.battery:5.1f}% | "
            f"Comb: {t.fuel:5.1f}% | "
            f"Rx: {self._potencia_rx_atual:8.1f} dBm | "
            f"Casco: {self._hull_temp:6.0f}°C | "
            f"Temp: {t.module_temp:5.1f}°C"
        )
