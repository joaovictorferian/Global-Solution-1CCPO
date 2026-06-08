class MissionReport:

    NOME_MISSAO = "Projeto Orion MCS"
    NOME_EQUIPE = "Equipe FIAP 1CCPO"

    AREAS_MONITORADAS = [
        "Temperatura dos módulos",
        "Comunicação com a Terra",
        "Sistema de energia",
        "Sistema de combustível",
        "Estabilidade estrutural",
    ]

    THRESHOLDS = {
        "Temperatura dos módulos":  {"atencao": 40.0,  "critico": 65.0,  "invertido": True},
        "Comunicação com a Terra":  {"atencao": 60.0,  "critico": 30.0,  "invertido": False},
        "Sistema de energia":       {"atencao": 50.0,  "critico": 20.0,  "invertido": False},
        "Sistema de combustível":   {"atencao": 40.0,  "critico": 15.0,  "invertido": False},
        "Estabilidade estrutural":  {"atencao": 80.0,  "critico": 50.0,  "invertido": False},
    }

    def __init__(self):
        self.dados_missao = []
        self.pontuacoes_risco = []
        self.classificacoes = []
        self.pontuacao_por_area = {area: 0 for area in self.AREAS_MONITORADAS}
        self.destino = ""

    def registrar_ciclo(self, telemetry, signal_percent):
        ciclo = [
            round(telemetry.module_temp, 1),
            round(signal_percent, 1),
            round(telemetry.battery, 1),
            round(telemetry.fuel, 1),
            round(telemetry.structural_integrity, 1),
        ]
        self.dados_missao.append(ciclo)

    @staticmethod
    def sinal_para_percentual(signal_dbm, rx_warning, rx_critical):
        if signal_dbm >= rx_warning:
            return 100.0
        elif signal_dbm <= rx_critical:
            return 0.0
        else:
            faixa = rx_warning - rx_critical
            return max(0.0, min(100.0, ((signal_dbm - rx_critical) / faixa) * 100.0))

    def _avaliar_area(self, area, valor):
        config = self.THRESHOLDS[area]

        if config["invertido"]:
            if valor >= config["critico"]:
                return "CRÍTICO", self._descricao_critica(area)
            elif valor >= config["atencao"]:
                return "ATENÇÃO", self._descricao_atencao(area)
            else:
                return "NORMAL", self._descricao_normal(area)
        else:
            if valor <= config["critico"]:
                return "CRÍTICO", self._descricao_critica(area)
            elif valor <= config["atencao"]:
                return "ATENÇÃO", self._descricao_atencao(area)
            else:
                return "NORMAL", self._descricao_normal(area)

    def _descricao_normal(self, area):
        descricoes = {
            "Temperatura dos módulos":  "Temperatura estável",
            "Comunicação com a Terra":  "Comunicação estável",
            "Sistema de energia":       "Energia estável",
            "Sistema de combustível":   "Combustível adequado",
            "Estabilidade estrutural":  "Estabilidade operacional adequada",
        }
        return descricoes.get(area, "Estável")

    def _descricao_atencao(self, area):
        descricoes = {
            "Temperatura dos módulos":  "Temperatura fora do intervalo ideal",
            "Comunicação com a Terra":  "Comunicação instável",
            "Sistema de energia":       "Bateria abaixo do recomendado",
            "Sistema de combustível":   "Combustível abaixo do recomendado",
            "Estabilidade estrutural":  "Estabilidade operacional reduzida",
        }
        return descricoes.get(area, "Atenção")

    def _descricao_critica(self, area):
        descricoes = {
            "Temperatura dos módulos":  "Risco de falha térmica",
            "Comunicação com a Terra":  "Comunicação em nível crítico",
            "Sistema de energia":       "Bateria em nível crítico",
            "Sistema de combustível":   "Combustível em nível crítico",
            "Estabilidade estrutural":  "Estabilidade operacional crítica",
        }
        return descricoes.get(area, "Crítico")

    def _calcular_risco_ciclo(self, ciclo):
        risco = 0
        unidades = ["°C", "%", "%", "%", "%"]

        for indice, area in enumerate(self.AREAS_MONITORADAS):
            valor = ciclo[indice]
            status, _ = self._avaliar_area(area, valor)

            if status == "ATENÇÃO":
                risco += 1
                self.pontuacao_por_area[area] += 1
            elif status == "CRÍTICO":
                risco += 2
                self.pontuacao_por_area[area] += 2

        return risco

    def _classificar_ciclo(self, risco):
        if risco >= 6:
            return "MISSÃO CRÍTICA"
        elif risco >= 3:
            return "MISSÃO EM ATENÇÃO"
        else:
            return "MISSÃO ESTÁVEL"

    def _recomendar(self, classificacao, ciclo):
        if classificacao == "MISSÃO CRÍTICA":
            return ("Ativar modo de segurança e priorizar suporte vital, "
                    "energia e comunicação.")
        elif classificacao == "MISSÃO EM ATENÇÃO":
            return ("Monitorar sistemas em atenção e preparar plano de "
                    "contingência.")
        else:
            return "Manter operação normal e continuar monitoramento."

    def _analisar_tendencia(self):
        if len(self.pontuacoes_risco) < 2:
            return "Dados insuficientes para análise de tendência."

        metade = len(self.pontuacoes_risco) // 2
        media_primeira = sum(self.pontuacoes_risco[:metade]) / metade
        media_segunda = sum(self.pontuacoes_risco[metade:]) / (len(self.pontuacoes_risco) - metade)

        if media_segunda > media_primeira + 0.5:
            return "A missão apresentou tendência de piora."
        elif media_segunda < media_primeira - 0.5:
            return "A missão apresentou tendência de melhora."
        else:
            return "A missão manteve-se estável ao longo das classificações."

    def _area_mais_afetada(self):
        maior_pontuacao = max(self.pontuacao_por_area.values())
        if maior_pontuacao == 0:
            return "Nenhuma área apresentou problemas significativos."

        for area, pontuacao in self.pontuacao_por_area.items():
            if pontuacao == maior_pontuacao:
                return area

    def _imprimir_ciclo(self, numero, ciclo, risco, classificacao):
        unidades = ["°C", "%", "%", "%", "%"]

        print(f"CICLO {numero}")
        print("-" * 60)

        for indice, area in enumerate(self.AREAS_MONITORADAS):
            valor = ciclo[indice]
            unidade = unidades[indice]
            status, descricao = self._avaliar_area(area, valor)

            if unidade == "°C":
                valor_fmt = f"{valor:.1f} {unidade}"
            else:
                valor_fmt = f"{valor:.1f}{unidade}"

            print(f"  {area}: {valor_fmt:>12} | {status:<8} | {descricao}")

        print(f"  Pontuação de risco do ciclo: {risco}")
        print(f"  Classificação do ciclo: {classificacao}")
        print(f"  Recomendação: {self._recomendar(classificacao, ciclo)}")
        print()

    def gerar_relatorio(self, destino, telemetry_log=None):
        self.destino = destino

        if len(self.dados_missao) == 0:
            print("Nenhum dado coletado para o relatório.")
            return

        for ciclo in self.dados_missao:
            risco = self._calcular_risco_ciclo(ciclo)
            classificacao = self._classificar_ciclo(risco)
            self.pontuacoes_risco.append(risco)
            self.classificacoes.append(classificacao)

        print()
        print("=" * 60)
        print("  Orion MCS")
        print("=" * 60)
        print(f"  Missão: {self.NOME_MISSAO}")
        print(f"  Equipe: {self.NOME_EQUIPE}")
        print(f"  Destino: {destino}")
        print(f"  Ciclos analisados: {len(self.dados_missao)}")
        print("=" * 60)
        print()

        for numero, ciclo in enumerate(self.dados_missao, start=1):
            risco = self.pontuacoes_risco[numero - 1]
            classificacao = self.classificacoes[numero - 1]
            self._imprimir_ciclo(numero, ciclo, risco, classificacao)

        print("=" * 60)
        print("  RELATÓRIO FINAL DA MISSÃO")
        print("=" * 60)
        print(f"  Missão: {self.NOME_MISSAO}")
        print(f"  Equipe: {self.NOME_EQUIPE}")
        print(f"  Destino: {destino}")
        print(f"  Ciclos analisados: {len(self.dados_missao)}")
        print()

        medias = []
        for indice, area in enumerate(self.AREAS_MONITORADAS):
            valores = [ciclo[indice] for ciclo in self.dados_missao]
            media = sum(valores) / len(valores)
            medias.append(media)
            unidade = "°C" if indice == 0 else "%"
            print(f"  Média de {area}: {media:.2f} {unidade}")

        print()

        risco_max = max(self.pontuacoes_risco)
        ciclo_critico = self.pontuacoes_risco.index(risco_max) + 1
        print(f"  Ciclo mais crítico: Ciclo {ciclo_critico}")
        print(f"  Maior pontuação de risco: {risco_max}")
        print(f"  Risco médio da missão: {sum(self.pontuacoes_risco) / len(self.pontuacoes_risco):.2f}")
        print(f"  Ciclos críticos: {self.classificacoes.count('MISSÃO CRÍTICA')}")
        print()

        print(f"  Tendência da missão:")
        print(f"    {self._analisar_tendencia()}")
        print()

        print("  Pontuação acumulada por área:")
        for area, pontuacao in self.pontuacao_por_area.items():
            print(f"    {area}: {pontuacao} pontos")
        print()

        print(f"  Área mais afetada:")
        print(f"    {self._area_mais_afetada()}")
        print()

        risco_medio = sum(self.pontuacoes_risco) / len(self.pontuacoes_risco)
        if risco_medio >= 5:
            classificacao_final = "MISSÃO CRÍTICA"
        elif risco_medio >= 2:
            classificacao_final = "MISSÃO EM ATENÇÃO"
        else:
            classificacao_final = "MISSÃO ESTÁVEL"

        print(f"  Classificação final da missão:")
        print(f"    {classificacao_final}")
        print()

        print("  Conclusão:")
        if classificacao_final == "MISSÃO CRÍTICA":
            print("    A missão enfrentou condições críticas em múltiplos sistemas.")
            print("    Recomenda-se revisão completa dos subsistemas afetados antes")
            print("    de autorizar nova operação.")
        elif classificacao_final == "MISSÃO EM ATENÇÃO":
            print("    A missão apresentou instabilidade relevante durante a operação.")
            print("    A equipe deve manter o plano de contingência ativo e monitorar")
            print("    os sistemas que apresentaram degradação.")
        elif classificacao_final == "MISSÃO ESTÁVEL":
            print("    A missão foi concluída dentro dos parâmetros operacionais esperados.")
            print("    Todos os sistemas mantiveram níveis aceitáveis ao longo da operação.")
        print()
        print("=" * 60)

        if telemetry_log:
            print()
            print("=" * 60)
            print("  LOG DE EVENTOS")
            print("=" * 60)
            for entrada in telemetry_log:
                print(f"    → {entrada}")
            print("=" * 60)

    def gerar_dados_frontend(self):
        if len(self.dados_missao) == 0:
            return None

        if len(self.pontuacoes_risco) == 0:
            for ciclo in self.dados_missao:
                risco = self._calcular_risco_ciclo(ciclo)
                classificacao = self._classificar_ciclo(risco)
                self.pontuacoes_risco.append(risco)
                self.classificacoes.append(classificacao)

        risco_medio = sum(self.pontuacoes_risco) / len(self.pontuacoes_risco)
        if risco_medio >= 5:
            classificacao_final = "MISSÃO CRÍTICA"
        elif risco_medio >= 2:
            classificacao_final = "MISSÃO EM ATENÇÃO"
        else:
            classificacao_final = "MISSÃO ESTÁVEL"

        risco_max = max(self.pontuacoes_risco)
        ciclo_critico = self.pontuacoes_risco.index(risco_max) + 1

        medias = {}
        unidades = ["°C", "%", "%", "%", "%"]
        for indice, area in enumerate(self.AREAS_MONITORADAS):
            valores = [ciclo[indice] for ciclo in self.dados_missao]
            medias[area] = round(sum(valores) / len(valores), 1)

        return {
            "ciclos_analisados": len(self.dados_missao),
            "classificacao_final": classificacao_final,
            "risco_medio": round(risco_medio, 2),
            "ciclo_critico": ciclo_critico,
            "risco_max": risco_max,
            "ciclos_criticos": self.classificacoes.count("MISSÃO CRÍTICA"),
            "tendencia": self._analisar_tendencia(),
            "area_mais_afetada": self._area_mais_afetada(),
            "medias": medias,
            "pontuacao_por_area": self.pontuacao_por_area,
        }