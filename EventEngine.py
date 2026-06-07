import random
import time
from AdvisorAI import recomendar_acao
from EventCatalog import EventCatalog
from playsound import playsound


class EventEngine:

    def __init__(self, destino, fase_atual, cascade, callbacks=None):
        self.callbacks = callbacks or {}
        self.cascade = cascade
        self.eventCatalog = EventCatalog
        self.destino = destino
        self.fase_atual = fase_atual

        if destino == "Marte":
            self.intervalo_sorteio = self.eventCatalog.INTERVALO_SORTEIO_MARTE
        else:
            self.intervalo_sorteio = self.eventCatalog.INTERVALO_SORTEIO_PADRAO

        self.eventos_ativos = []

    def sortear_evento(self, telemetry, tick_atual):
        if tick_atual == 0 or tick_atual % self.intervalo_sorteio != 0:
            return

        if random.random() > self.eventCatalog.CHANCE_EVENTO_POR_SORTEIO:
            return

        eventos_validos = []
        for evento in self.eventCatalog.CATALOGO_EVENTOS:
            if self.fase_atual in evento["fases_ativas"]:
                eventos_validos.append(evento)

        if not eventos_validos:
            return

        pesos = []
        for evento in eventos_validos:
            peso = evento["probabilidade_base"] * evento["peso_por_fase"].get(self.fase_atual, 1.0)
            pesos.append(peso)

        evento_sorteado = random.choices(eventos_validos, weights=pesos, k=1)[0]

        if self.callbacks.get("emitir_evento"):
            self.callbacks["emitir_evento"](evento_sorteado, evento_sorteado["opcoes_resposta"])

            # IA
            try:
                from AdvisorAI import recomendar_acao
                recomendacao = recomendar_acao(
                    evento_sorteado["nome"],
                    evento_sorteado["categoria"],
                    evento_sorteado["severidade"],
                    evento_sorteado["atributos_afetados"],
                    evento_sorteado["opcoes_resposta"],
                )
                if self.callbacks.get("emitir_ia"):
                    self.callbacks["emitir_ia"](str(recomendacao))
            except Exception:
                pass

            # aguarda resposta do frontend
            escolha = self.callbacks["aguardar_resposta"]()

        else:
            # modo terminal
            print("\n" + "!" * 70)
            print(f"  ⚠ EVENTO: {evento_sorteado['nome']}")
            print("!" * 70)

            print("\n  Opções de resposta:")
            for indice, opcao in enumerate(evento_sorteado["opcoes_resposta"]):
                print(f"    [{indice + 1}] {opcao['descricao']}")

            escolha = 0
            while escolha < 1 or escolha > len(evento_sorteado["opcoes_resposta"]):
                try:
                    escolha = int(input("\n  Escolha a ação (número): "))
                except ValueError:
                    escolha = 0
                if escolha < 1 or escolha > len(evento_sorteado["opcoes_resposta"]):
                    print("  Opção inválida!")
            escolha = escolha - 1

        acao_escolhida = evento_sorteado["opcoes_resposta"][escolha]

        time.sleep(5)

        self.eventos_ativos.append({
            "evento": evento_sorteado,
            "acao_escolhida": acao_escolhida,
            "tick_inicio": tick_atual,
        })

        if self.callbacks.get("emitir_log"):
            self.callbacks["emitir_log"](
                f"EVENTO — {evento_sorteado['nome']} | Ação: {acao_escolhida['descricao']}",
                "warn"
            )

        telemetry.log(
            f"[Tick {tick_atual} | {self.fase_atual}] EVENTO — {evento_sorteado['nome']} | Ação: {acao_escolhida['descricao']}"
        )

    def processar_eventos_ativos(self, telemetry, tick_atual):
        eventos_resolvidos = []

        for evento_ativo in self.eventos_ativos:
            evento = evento_ativo["evento"]
            acao_escolhida = evento_ativo["acao_escolhida"]
            tick_inicio = evento_ativo["tick_inicio"]
            ticks_restantes = (tick_inicio + evento["ticks_para_resolver"]) - tick_atual

            if ticks_restantes > 0:
                # aplica dano contínuo por tick
                dano_por_tick = (evento["impacto_base"] * evento["severidade"]) / evento["ticks_para_resolver"]

                for atributo in evento["atributos_afetados"]:
                    valor_atual = getattr(telemetry, atributo)
                    setattr(telemetry, atributo, valor_atual - dano_por_tick)
                    self.cascade.propagar(telemetry, atributo, dano_por_tick, callbacks=self.callbacks)

            else:
                # resolução concluída — aplica mitigação ou agravamento
                impacto_final = self._calcular_impacto(evento, acao_escolhida)

                for atributo in evento["atributos_afetados"]:
                    valor_atual = getattr(telemetry, atributo)
                    setattr(telemetry, atributo, valor_atual + impacto_final)

                telemetry.log(
                    f"[Tick {tick_atual} | {self.fase_atual}] RESOLVIDO — {evento['nome']} | "
                    f"Recuperação: {impacto_final:.1f}"
                )
                if self.callbacks.get("emitir_evento_resolvido"):
                    self.callbacks["emitir_evento_resolvido"](evento['nome'], impacto_final)
                eventos_resolvidos.append(evento_ativo)

        for resolvido in eventos_resolvidos:
            self.eventos_ativos.remove(resolvido)


    def _calcular_impacto(self, evento, acao_escolhida):
        dano_total = evento["impacto_base"] * evento["severidade"]
        nivel_mitigacao = acao_escolhida["nivel_mitigacao"]

        if nivel_mitigacao == "alta":
            fator_mitigacao = random.uniform(*self.eventCatalog.FAIXA_MITIGACAO_ALTA)
            recuperacao = dano_total * fator_mitigacao
            return recuperacao

        elif nivel_mitigacao == "media":
            fator_mitigacao = random.uniform(*self.eventCatalog.FAIXA_MITIGACAO_MEDIA)
            recuperacao = dano_total * fator_mitigacao
            return recuperacao

        else:
            if acao_escolhida["agrava"]:
                fator_agravamento = random.uniform(*self.eventCatalog.FAIXA_AGRAVAMENTO_OMISSAO)
                penalidade = dano_total * fator_agravamento
                return penalidade
            return 0.0
