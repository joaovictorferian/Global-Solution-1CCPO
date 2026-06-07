import matplotlib.pyplot as plt

class Dashboard:

    def __init__(self):
        self.tempos      = []
        self.bateria     = []
        self.combustivel = []
        self.sinal       = []
        self.temperatura = []
        self.radiacao     = []
        self.fases       = []
        self._tempo_total = 0

    def registrar(self, duracao_tick, telemetry, fase):
        self._tempo_total += duracao_tick
        self.tempos.append(self._tempo_total)
        self.bateria.append(telemetry.battery)
        self.combustivel.append(telemetry.fuel)
        self.sinal.append(telemetry.signal)
        self.temperatura.append(telemetry.module_temp)
        self.radiacao.append(telemetry.radiation_exposure)
        self.fases.append(fase)

    def exibir(self, destino):
        fig, eixos = plt.subplots(5, 1, figsize=(14, 16), sharex=True)
        fig.suptitle(f"Mission Control AI — {destino}", fontsize=16, fontweight="bold")

        cores_fase = {
            "launch":    "#FF6B6B",
            "transit":   "#4ECDC4",
            "operation": "#45B7D1",
            "return":    "#96CEB4",
        }

        # pinta fundo por fase
        for eixo in eixos:
            fase_atual = None
            inicio_fase = 0
            for indice, fase in enumerate(self.fases):
                if fase != fase_atual:
                    if fase_atual is not None:
                        eixo.axvspan(
                            self.tempos[inicio_fase],
                            self.tempos[indice - 1],
                            alpha=0.1,
                            color=cores_fase.get(fase_atual, "#CCCCCC"),
                        )
                    fase_atual = fase
                    inicio_fase = indice
            if fase_atual is not None:
                eixo.axvspan(
                    self.tempos[inicio_fase],
                    self.tempos[-1],
                    alpha=0.1,
                    color=cores_fase.get(fase_atual, "#CCCCCC"),
                )

        # bateria
        eixos[0].plot(self.tempos, self.bateria, color="#FF6B6B", linewidth=1.5)
        eixos[0].set_ylabel("Bateria (%)")
        eixos[0].set_ylim(-5, 105)
        eixos[0].axhline(y=30, color="orange", linestyle="--", alpha=0.5, label="Warning")
        eixos[0].axhline(y=10, color="red", linestyle="--", alpha=0.5, label="Critical")
        eixos[0].legend(loc="upper right", fontsize=8)

        # combustivel
        eixos[1].plot(self.tempos, self.combustivel, color="#4ECDC4", linewidth=1.5)
        eixos[1].set_ylabel("Combustível (%)")
        eixos[1].set_ylim(-5, 105)
        eixos[1].axhline(y=15, color="orange", linestyle="--", alpha=0.5, label="Warning")
        eixos[1].axhline(y=5, color="red", linestyle="--", alpha=0.5, label="Critical")
        eixos[1].legend(loc="upper right", fontsize=8)

        # sinal
        eixos[2].plot(self.tempos, self.sinal, color="#45B7D1", linewidth=1.5)
        eixos[2].set_ylabel("Sinal (dBm)")
        eixos[2].legend(["Rx (dBm)"], loc="upper right", fontsize=8)

        # temperatura
        eixos[3].plot(self.tempos, self.temperatura, color="#F39C12", linewidth=1.5)
        eixos[3].set_ylabel("Temperatura (°C)")
        eixos[3].axhline(y=60, color="orange", linestyle="--", alpha=0.5, label="Warning")
        eixos[3].axhline(y=-60, color="blue", linestyle="--", alpha=0.5, label="Warning frio")
        eixos[3].legend(loc="upper right", fontsize=8)

        # radiação
        eixos[4].plot(self.tempos, self.radiacao, color="#9B59B6", linewidth=1.5)
        eixos[4].set_ylabel("Radiação (mSv)")
        eixos[4].set_xlabel("Tempo (h)")
        eixos[4].axhline(y=200, color="orange", linestyle="--", alpha=0.5, label="Warning")
        eixos[4].legend(loc="upper right", fontsize=8)

        plt.tight_layout()
        plt.savefig("dashboard_missao.png", dpi=150, bbox_inches="tight")
        plt.show()