import random

class CascadeFailure:

    GRAFO_DEPENDENCIAS = {
        "battery": {
            "dependentes": ["signal", "fuel"],
            "faixa_propagacao": (0.20, 0.40),
        },
        "structural_integrity": {
            "dependentes": ["battery", "signal"],
            "faixa_propagacao": (0.15, 0.35),
        },
        "signal": {
            "dependentes": [],
            "faixa_propagacao": (0.0, 0.0),
        },
        "fuel": {
            "dependentes": [],
            "faixa_propagacao": (0.0, 0.0),
        },
    }

    def propagar(self, telemetry, atributo_origem, dano, sistemas_afetados=None):
        if sistemas_afetados is None:
            sistemas_afetados = set()

        sistemas_afetados.add(atributo_origem)

        dependencia = self.GRAFO_DEPENDENCIAS.get(atributo_origem)
        if not dependencia:
            return

        for dependente in dependencia["dependentes"]:
            if dependente in sistemas_afetados:
                continue

            fator_propagacao = random.uniform(*dependencia["faixa_propagacao"])
            dano_propagado   = dano * fator_propagacao
            valor_atual      = getattr(telemetry, dependente)
            setattr(telemetry, dependente, valor_atual - dano_propagado)

            telemetry.log(
                f"[CASCADE] {atributo_origem} → {dependente} | "
                f"Dano propagado: {dano_propagado:.1f}"
            )

            print(
                f"  ⚡ [CASCADE] {atributo_origem} → {dependente} | "
                f"Dano propagado: {dano_propagado:.1f}"
            )

            self.propagar(telemetry, dependente, dano_propagado, sistemas_afetados)