import random
import math
import time
from pip._internal.operations import check


class Operation:
    # fator solar fixo por destino (lei do inverso do quadrado)
    # Fonte: NASA Mars Surface Power Decision (2024)
    CAPACIDADE_BATERIA_KWH = 200.0

    FATOR_SOLAR_DESTINO = {
        "LEO": 1.00,
        "Lua": 0.99,
        "Marte": 0.43,
    }

    # consumo de instrumentos calibrado para manter ratios reais por destino
    # Referência: Apollo CSM ~2.2kW (geração ≈ consumo nominal)
    # LEO: saldo positivo | Lua: déficit lento | Marte: colapso sem nuclear
    CONSUMO_INSTRUMENTOS_W = {
        "LEO": 8.0,
        "Lua": 18.0,
        "Marte": 30.0,
    }

    def __init__(self, telemetry, duration, destino, perfil_nave, event_engine,callbacks=None ):
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
        self.fator_solar = self.FATOR_SOLAR_DESTINO.get(destino, 1.0)
        self.consumo_instr = self.CONSUMO_INSTRUMENTOS_W.get(destino, 18.0)
        self.frequencia_mhz = perfil_nave["frequencia_mhz"]
        self.potencia_tx_dbm = perfil_nave["potencia_tx_dbm"]
        self.rx_warning_dbm = perfil_nave["rx_warning_dbm"]
        self.rx_critical_dbm = perfil_nave["rx_critical_dbm"]
        self.distancia_km = perfil_nave["distancia_km"]

        match self.destino:
            case "Marte":
                self.intervalo = 10
            case "LEO":
                self.intervalo = 10
            case _:
                self.intervalo = 20

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
        self._potencia_rx_atual = 0.0

        # reseta status se a fase anterior terminou em warning/critical
        # por condição que não persiste (ex: sinal fraco no trânsito)
        if self.telemetry.status != "nominal":
            self.telemetry.status = "nominal"

        self._check_alerts()

    # ─── FSPL fixo na distância do destino ───────────────────────

    def _potencia_rx(self):
        perda = (20 * math.log10(self.distancia_km)
                 + 20 * math.log10(self.frequencia_mhz)
                 + 32.44)
        ruido = random.uniform(-1.5, 1.5)
        return self.potencia_tx_dbm - perda + ruido

    # ─── loop principal ──────────────────────────────────────────

    def run(self):
        geracao_solar_media = self.geracao_solar_kw * self.fator_solar
        geracao_nuclear_media = self.geracao_nuclear_kw if self.geracao_nuclear_kw > 0 else 0.0
        geracao_media = geracao_solar_media + geracao_nuclear_media
        consumo_medio = self.consumo_base_kw + self.consumo_comms_kw
        saldo = geracao_media - consumo_medio

        print("\n" + "═" * 70)
        print("  FASE 3 — OPERAÇÃO")
        print(f"  Destino  : {self.destino} | Solar fixo: {self.fator_solar * 100:.0f}%")
        print(f"  Energia  : Solar ~{geracao_solar_media:.1f} kW | Nuclear ~{geracao_nuclear_media:.0f} kW")
        print(f"  Consumo  : ~{consumo_medio:.1f} kW | Saldo {saldo:+.1f} kW")
        print(f"  Bateria  : {self.CAPACIDADE_BATERIA_KWH:.0f} kWh")
        print(f"  Duração  : {self.duration}h | 1 tick = {self.horas_por_tick}h | Total: {self.total_ticks} ticks")
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
                        "fator_solar": self.fator_solar,
                        "nuclear_ativa": self.nuclear_ativa,
                        "geracao_solar_kw": round(self._geracao_solar_atual, 1),
                        "geracao_nuclear_kw": round(self._geracao_nuclear_atual, 0),
                        "geracao_total_kw": round(self._geracao_total_atual, 1),
                        "consumo_total_kw": round(self._consumo_total_atual, 1),
                    }
                )

            self.tick += 1

            if self.telemetry.status == "critical":
                print("\n  ✖ Situação crítica durante a operação.")
                break

            if self.telemetry.battery == 0.0:
                print("  ✖ Bateria em estado crítico! Impossível prosseguir com a missão...")
                self.telemetry.sucesso = False
                return self.telemetry

        print("\n  Operação concluída.")
        return self.telemetry

    # ─── atualiza os valores a cada tick ─────────────────────────

    def _update(self):
        t = self.telemetry
        dt = self.horas_por_tick

        self._potencia_rx_atual = self._potencia_rx()
        t.signal = self._potencia_rx_atual

        geracao_solar_kw = self.geracao_solar_kw * self.fator_solar * random.uniform(0.85, 1.15)

        nuclear_desativada = False
        for evento_ativo in self.event_engine.eventos_ativos:
            if evento_ativo["evento"].get("desativa_nuclear", False):
                nuclear_desativada = True
                break

        if self.nuclear_ativa and not nuclear_desativada:
            geracao_nuclear_kw = self.geracao_nuclear_kw * random.uniform(0.95, 1.05)
        else:
            geracao_nuclear_kw = 0.0

        geracao_total_kw = geracao_solar_kw + geracao_nuclear_kw

        consumo_base_kw = self.consumo_base_kw * random.uniform(0.90, 1.10)
        consumo_total_kw = consumo_base_kw + self.consumo_comms_kw

        temp_solar = 30.0 * self.fator_solar  # aquecimento solar
        temp_consumo = 10.0 * (consumo_base_kw / 4.0)
        temp_base = -40.0  # temperatura base com isolamento térmico
        temp_alvo = temp_base + temp_solar + temp_consumo
        t.module_temp += (temp_alvo - t.module_temp) * 0.01 * dt

        saldo_kw = geracao_total_kw - consumo_total_kw
        variacao_pct = (saldo_kw * dt / self.CAPACIDADE_BATERIA_KWH) * 100
        t.battery += variacao_pct
        t.battery = max(0.0, min(100.0, t.battery))

        # dentro de _update(), onde calcula a geração:
        self._geracao_solar_atual = geracao_solar_kw
        self._geracao_nuclear_atual = geracao_nuclear_kw
        self._consumo_total_atual = consumo_total_kw
        self._geracao_total_atual = geracao_solar_kw + geracao_nuclear_kw

        t.fuel -= 0.02 * dt
        t.fuel = max(0.0, t.fuel)

        rad_hora = 0.8 * random.uniform(0.80, 1.30)
        t.radiation_exposure += rad_hora * dt

    # ─── verifica alertas ─────────────────────────────────────────

    def _check_alerts(self):
        t = self.telemetry
        novo = False
        tempo = self.tick * self.horas_por_tick
        rx = self._potencia_rx_atual

        if t.battery <= 10.0:
            t.status = "critical"
            t.log(f"[T+{tempo}h | operação] CRÍTICO — Bateria em colapso: {t.battery:.1f}%")
            novo = True
        elif t.battery <= 30.0:
            if t.status == "nominal":
                t.status = "warning"
                t.log(f"[T+{tempo}h | operação] AVISO — Bateria baixa: {t.battery:.1f}%")
                novo = True

        if rx <= self.rx_critical_dbm:
            t.status = "critical"
            t.log(f"[T+{tempo}h | operação] CRÍTICO — Sinal perdido: {rx:.1f} dBm")
            novo = True
        elif rx <= self.rx_warning_dbm:
            if t.status == "nominal":
                t.status = "warning"
                t.log(f"[T+{tempo}h | operação] AVISO — Sinal fraco: {rx:.1f} dBm")
                novo = True

        if t.fuel <= 15.0:
            if t.status == "nominal":
                t.status = "warning"
                t.log(f"[T+{tempo}h | operação] AVISO — Combustível baixo para retorno: {t.fuel:.1f}%")
                novo = True

        if t.radiation_exposure >= 200.0:
            if t.status == "nominal":
                t.status = "warning"
                t.log(f"[T+{tempo}h | operação] AVISO — Radiação alta: {t.radiation_exposure:.1f} mSv")
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

    # ─── imprime conforme intervalo ou alerta ─────────────────────

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
            f"Solar: {self.fator_solar * 100:4.0f}% | "
            f"Bat: {t.battery:5.1f}% | "
            f"Comb: {t.fuel:5.1f}% | "
            f"Rx: {self._potencia_rx_atual:8.1f} dBm | "
            f"Rad: {rad:7.1f} mSv"
            f"Temp: {t.module_temp:5.1f}°C"
        )
