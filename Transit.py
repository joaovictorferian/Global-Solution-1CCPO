import random
import math
import time


class Transit:
    distanciaSolTerra = 150_000_000.0
    distanciaSolMarte = 228_000_000.0
    irrandinciaSolTerra = 1368.0
    magnetosfera = 60_000.0
    capacidadeBateria_KWH = 200.0
    distanciaParaAtivacaoNuclear = 152_000_000

    PERFIL_NAVE = {
        "LEO": {
            "distancia_km": 400,
            "frequencia_mhz": 437.0,
            "potencia_tx_dbm": 30,
            "rx_warning_dbm": -110.0,
            "rx_critical_dbm": -125.0,
            "consumo_comms_kw": 0.2,
            "geracao_solar_kw": 2.2,
            "consumo_base_kw": 1.5,
            "geracao_nuclear_kw": 0.0,
        },
        "Lua": {
            "distancia_km": 384_400,
            "frequencia_mhz": 2295.0,
            "potencia_tx_dbm": 60,
            "rx_warning_dbm": -145.0,
            "rx_critical_dbm": -155.0,
            "consumo_comms_kw": 0.5,
            "geracao_solar_kw": 2.2,
            "consumo_base_kw": 1.5,
            "geracao_nuclear_kw": 0.0,
        },
        "Marte": {
            "distancia_km": 250_000_000,
            "frequencia_mhz": 8415.0,
            "potencia_tx_dbm": 90,
            "rx_warning_dbm": -180.0,
            "rx_critical_dbm": -200.0,
            "consumo_comms_kw": 1.0,
            "geracao_solar_kw": 2.2,
            "consumo_base_kw": 3.0,
            "geracao_nuclear_kw": 90.0,
        },
    }

    def __init__(self, telemetry, duration, destino, event_engine, callbacks=None):
        self.callbacks = callbacks or {}
        self.telemetry = telemetry
        self.event_engine = event_engine
        self.duration = duration
        self.destino = destino
        self.tick = 0
        perfil = self.PERFIL_NAVE.get(destino)
        self.distance_traveled = 0.0
        self.distancia_total = perfil["distancia_km"]
        self.frequencia_mhz = perfil["frequencia_mhz"]
        self.potencia_tx_dbm = perfil["potencia_tx_dbm"]
        self.rx_warning_dbm = perfil["rx_warning_dbm"]
        self.rx_critical_dbm = perfil["rx_critical_dbm"]
        self.consumo_comms_kw = perfil["consumo_comms_kw"]
        self.consumo_base_kw = perfil["consumo_base_kw"]
        self.geracao_solar_kw = perfil["geracao_solar_kw"]
        self.geracao_nuclear_kw = perfil["geracao_nuclear_kw"]
        self.nuclear_ativa = False

        match self.destino:
            case "Marte":
                self.intervalo = 10
            case "LEO":
                self.intervalo = 10
            case "Lua":
                self.intervalo = 20

        if duration > 1000:
            self.horas_por_tick = 50
            self.intervalo_print = 20
        elif duration >200:
            self.horas_por_tick = 10
            self.intervalo_print = 100
        else:
            self.horas_por_tick = 1
            self.intervalo_print = 1

        self.total_ticks = duration // self.horas_por_tick
        self.velocidade_kmh = self.distancia_total / duration

        self._fator_solar_atual = 1.0
        self._potencia_rx_atual = 0.0

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
        progresso = min(1.0, self.distance_traveled / self.distancia_total)
        d_sol_atual = (self.distanciaSolTerra
                       + progresso * (self.distanciaSolMarte - self.distanciaSolTerra))
        return (self.distanciaSolTerra / d_sol_atual) ** 2

    def verificar_nuclear(self):
        if self.geracao_nuclear_kw == 0.0:
            self.nuclear_ativa = False
            return

        distancia_do_sol = self.distanciaSolTerra + self.distance_traveled
        self.nuclear_ativa = distancia_do_sol >= self.distanciaParaAtivacaoNuclear


    def run(self):
        banda = ("UHF" if self.frequencia_mhz < 1000
                 else "S-band" if self.frequencia_mhz < 4000
        else "X-band")
        print("\n" + "═" * 70)
        print("  FASE 2 — TRÂNSITO")
        print(f"  Destino    : {self.destino}")
        print(f"  Comunicação: {self.frequencia_mhz:.0f} MHz ({banda}) | Tx: {self.potencia_tx_dbm} dBm")
        print(f"  Energia    : Solar {self.geracao_solar_kw:.1f} kW | Nuclear {self.geracao_nuclear_kw:.0f} kW")
        print(f"  Consumo    : Base {self.consumo_base_kw:.1f} kW | Comms {self.consumo_comms_kw:.1f} kW")
        print(f"  Bateria    : {self.capacidadeBateria_KWH:.0f} kWh")
        print(f"  Duração    : {self.duration}h | 1 tick = {self.horas_por_tick}h | Total: {self.total_ticks} ticks")
        print("═" * 70)

        while self.tick < self.total_ticks:
            self._update()
            self.event_engine.sortear_evento(self.telemetry, self.tick)
            self.event_engine.processar_eventos_ativos(self.telemetry, self.tick)
            alertas_novos = self._check_alerts()

            if self.tick % self.intervalo == 00 and self.tick > 0:
                time.sleep(5)

            self._print_status(forcar=alertas_novos)

            print(f"[DEBUG] callbacks keys: {list(self.callbacks.keys())}")
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

            self.tick += 1

            if self.telemetry.status == "critical":
                print("\n  ✖ Situação crítica durante o trânsito.")
                break

            if self.telemetry.battery == 0.0:
                print("  ✖ Bateria em estado crítico! Impossível prosseguir com a missão...")
                self.telemetry.sucesso = False
                return self.telemetry
            elif self.telemetry.fuel == 0.0:
                print("  ✖ Combustível insuficiente para manobra! Impossível prosseguir com a missão...")
                self.telemetry.sucesso = False
                return self.telemetry

        print("\n  Trânsito concluído.")
        return self.telemetry
    

    def _update(self):
        telemetria = self.telemetry
        dt = self.horas_por_tick

        self.distance_traveled += self.velocidade_kmh * dt

        self._potencia_rx_atual = self._potencia_rx(self.distance_traveled)
        telemetria.signal = self._potencia_rx_atual

        fator = self._fator_solar()
        self._fator_solar_atual = fator

        geracao_solar_kw = self.geracao_solar_kw * fator * random.uniform(0.85, 1.15)

        nuclear_desativada = False
        for evento_ativo in self.event_engine.eventos_ativos:
            if evento_ativo["evento"].get("desativa_nuclear", False):
                nuclear_desativada = True
                break

        self.verificar_nuclear()
        if self.nuclear_ativa and not nuclear_desativada:
            geracao_nuclear_kw = self.geracao_nuclear_kw * random.uniform(0.95, 1.05)
        else:
            geracao_nuclear_kw = 0.0

        geracao_total_kw = geracao_solar_kw + geracao_nuclear_kw

        consumo_base_kw = self.consumo_base_kw * random.uniform(0.90, 1.10)
        consumo_total_kw = consumo_base_kw + self.consumo_comms_kw


        temp_solar = 30.0 * self._fator_solar_atual  
        temp_consumo = 10.0 * (consumo_base_kw / 4.0)
        temp_base = -40.0  
        temp_alvo = temp_base + temp_solar + temp_consumo
        telemetria.module_temp += (temp_alvo - telemetria.module_temp) * 0.01 * dt

        saldo_kw = geracao_total_kw - consumo_total_kw
        variacao_pct = (saldo_kw * dt / self.capacidadeBateria_KWH) * 100
        telemetria.battery += variacao_pct
        telemetria.battery = max(0.0, min(100.0, telemetria.battery))

        self._geracao_solar_atual = geracao_solar_kw
        self._geracao_nuclear_atual = geracao_nuclear_kw
        self._consumo_total_atual = consumo_total_kw
        self._geracao_total_atual = geracao_solar_kw + geracao_nuclear_kw

        telemetria.fuel -= 0.5

        if self.distance_traveled < self.magnetosfera:
            rad_hora = 0.3 + 0.3 * (self.distance_traveled / self.magnetosfera)
        else:
            excesso = self.distance_traveled - self.magnetosfera
            rad_hora = 0.6 + (excesso / 200_000.0)
            rad_hora = min(rad_hora, 4.0)

        rad_hora *= random.uniform(0.80, 1.30)
        telemetria.radiation_exposure += rad_hora * dt


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

        if t.radiation_exposure >= 200.0:
            if t.status == "nominal":
                t.status = "warning"
                t.log(f"[T+{tempo}h] AVISO — Radiação alta: {t.radiation_exposure:.1f} mSv")
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

        telemetria = self.telemetry
        tempo = self.tick * self.horas_por_tick
        icons = {"nominal": "✓", "warning": "⚠", "critical": "✖"}
        icon = icons.get(telemetria.status, "?")
        nuclear = "ON" if self.nuclear_ativa else "OFF"

        print(
            f"  T+{tempo:6.0f}h {icon} | "
            f"Solar: {self._fator_solar_atual * 100:4.0f}% | "
            f"Nuclear: {nuclear} | "
            f"Bat: {telemetria.battery:5.1f}% | "
            f"Comb: {telemetria.fuel:5.1f}% | "
            f"Rx: {self._potencia_rx_atual:8.1f} dBm | "
            f"Rad: {telemetria.radiation_exposure:7.1f} mSv"
            f"Temp: {telemetria.module_temp:5.1f}°C"
        )