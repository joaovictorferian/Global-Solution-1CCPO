class EventCatalog:

    INTERVALO_SORTEIO_PADRAO = 10
    INTERVALO_SORTEIO_MARTE  = 5

    CHANCE_EVENTO_POR_SORTEIO = 0.30

    FAIXA_MITIGACAO_ALTA      = (0.55, 0.85)
    FAIXA_MITIGACAO_MEDIA     = (0.25, 0.50)
    FAIXA_AGRAVAMENTO_OMISSAO = (-0.10, -0.30)

    CATALOGO_EVENTOS = [
        {
            "nome"               : "Falha no motor principal",
            "categoria"          : "Engine",
            "severidade"         : 4,
            "atributos_afetados" : ["fuel"],
            "impacto_base"       : 2.0,
            "probabilidade_base" : 0.30,
            "fases_ativas"       : ["launch", "transit", "return"],
            "peso_por_fase"      : {"launch": 2.0, "transit": 1.0, "return": 1.5},
            "ticks_para_resolver": 3,
            "opcoes_resposta"    : [
                {"descricao": "Isolar motor secundário",  "nivel_mitigacao": "alta",   "agrava": False},
                {"descricao": "Reduzir empuxo",           "nivel_mitigacao": "media",  "agrava": False},
                {"descricao": "Não agir",                 "nivel_mitigacao": "nenhuma","agrava": False},
            ]
        },
        {
            "nome"               : "Vazamento de propelente",
            "categoria"          : "Engine",
            "severidade"         : 3,
            "atributos_afetados" : ["fuel"],
            "impacto_base"       : 2.0,
            "probabilidade_base" : 0.25,
            "fases_ativas"       : ["launch", "transit", "return"],
            "peso_por_fase"      : {"launch": 2.0, "transit": 1.5, "return": 1.5},
            "ticks_para_resolver": 4,
            "opcoes_resposta"    : [
                {"descricao": "Selar válvula de contenção", "nivel_mitigacao": "alta",   "agrava": False},
                {"descricao": "Redirecionar fluxo",         "nivel_mitigacao": "media",  "agrava": False},
                {"descricao": "Não agir",                   "nivel_mitigacao": "nenhuma","agrava": True},
            ]
        },
        {
            "nome"               : "Falha no painel solar",
            "categoria"          : "Power",
            "severidade"         : 3,
            "atributos_afetados" : ["battery"],
            "impacto_base"       : 3.0,
            "probabilidade_base" : 0.25,
            "fases_ativas"       : ["transit", "operation"],
            "peso_por_fase"      : {"transit": 1.0, "operation": 2.0},
            "ticks_para_resolver": 3,
            "opcoes_resposta"    : [
                {"descricao": "Reorientar painel reserva",       "nivel_mitigacao": "alta",   "agrava": False},
                {"descricao": "Desligar sistemas não essenciais", "nivel_mitigacao": "media",  "agrava": False},
                {"descricao": "Não agir",                        "nivel_mitigacao": "nenhuma","agrava": False},
            ]
        },
        {
            "nome"               : "Sobrecarga elétrica",
            "categoria"          : "Power",
            "severidade"         : 2,
            "atributos_afetados" : ["battery"],
            "impacto_base"       : 3.0,
            "probabilidade_base" : 0.20,
            "fases_ativas"       : ["launch", "transit", "operation", "return"],
            "peso_por_fase"      : {"launch": 1.0, "transit": 1.0, "operation": 2.0, "return": 1.0},
            "ticks_para_resolver": 2,
            "opcoes_resposta"    : [
                {"descricao": "Redirecionar carga elétrica",     "nivel_mitigacao": "alta",   "agrava": False},
                {"descricao": "Desligar sistemas secundários",    "nivel_mitigacao": "media",  "agrava": False},
                {"descricao": "Não agir",                        "nivel_mitigacao": "nenhuma","agrava": True},
            ]
        },
        {
            "nome"               : "Perda de conexão com os sistemas de comunicação da terra",
            "categoria"          : "Communication",
            "severidade"         : 3,
            "atributos_afetados" : ["signal"],
            "impacto_base"       : 2.0,
            "probabilidade_base" : 0.25,
            "fases_ativas"       : ["transit", "operation", "return"],
            "peso_por_fase"      : {"transit": 2.0, "operation": 1.5, "return": 2.0},
            "ticks_para_resolver": 3,
            "opcoes_resposta"    : [
                {"descricao": "Reorientar antena direcional",     "nivel_mitigacao": "alta",   "agrava": False},
                {"descricao": "Aumentar potência de transmissão", "nivel_mitigacao": "media",  "agrava": False},
                {"descricao": "Não agir",                        "nivel_mitigacao": "nenhuma","agrava": False},
            ]
        },
        {
            "nome"               : "Interferência eletromagnética",
            "categoria"          : "Communication",
            "severidade"         : 2,
            "atributos_afetados" : ["signal"],
            "impacto_base"       : 2.0,
            "probabilidade_base" : 0.20,
            "fases_ativas"       : ["launch", "transit", "operation", "return"],
            "peso_por_fase"      : {"launch": 1.0, "transit": 1.0, "operation": 2.0, "return": 1.0},
            "ticks_para_resolver": 2,
            "opcoes_resposta"    : [
                {"descricao": "Ativar filtro de interferência",   "nivel_mitigacao": "alta",   "agrava": False},
                {"descricao": "Mudar frequência de operação",     "nivel_mitigacao": "media",  "agrava": False},
                {"descricao": "Não agir",                        "nivel_mitigacao": "nenhuma","agrava": False},
            ]
        },
        {
            "nome"               : "Micro-impacto de meteorito",
            "categoria"          : "Structures",
            "severidade"         : 3,
            "atributos_afetados" : ["structural_integrity"],
            "impacto_base"       : 2.5,
            "probabilidade_base" : 0.20,
            "fases_ativas"       : ["transit", "operation", "return"],
            "peso_por_fase"      : {"transit": 2.0, "operation": 1.0, "return": 2.0},
            "ticks_para_resolver": 4,
            "opcoes_resposta"    : [
                {"descricao": "Acionar protocolo de contenção",   "nivel_mitigacao": "alta",   "agrava": False},
                {"descricao": "Monitorar e aguardar",             "nivel_mitigacao": "media",  "agrava": False},
                {"descricao": "Não agir",                        "nivel_mitigacao": "nenhuma","agrava": True},
            ]
        },
        {
            "nome"               : "Fadiga estrutural",
            "categoria"          : "Structures",
            "severidade"         : 2,
            "atributos_afetados" : ["structural_integrity"],
            "impacto_base"       : 2.5,
            "probabilidade_base" : 0.15,
            "fases_ativas"       : ["transit", "operation", "return"],
            "peso_por_fase"      : {"transit": 2.0, "operation": 1.0, "return": 2.0},
            "ticks_para_resolver": 5,
            "opcoes_resposta"    : [
                {"descricao": "Reforçar estrutura com selante",   "nivel_mitigacao": "alta",   "agrava": False},
                {"descricao": "Redistribuir carga estrutural",    "nivel_mitigacao": "media",  "agrava": False},
                {"descricao": "Não agir",                        "nivel_mitigacao": "nenhuma","agrava": True},
            ]
        },
        {
            "nome"               : "Falha no controle de atitude",
            "categoria"          : "AD&C",
            "severidade"         : 3,
            "atributos_afetados" : ["signal", "fuel"],
            "impacto_base"       : 2.0,
            "probabilidade_base" : 0.20,
            "fases_ativas"       : ["transit", "operation", "return"],
            "peso_por_fase"      : {"transit": 1.0, "operation": 2.0, "return": 2.0},
            "ticks_para_resolver": 3,
            "opcoes_resposta"    : [
                {"descricao": "Ativar sistema de controle redundante", "nivel_mitigacao": "alta",   "agrava": False},
                {"descricao": "Correção manual de trajetória",         "nivel_mitigacao": "media",  "agrava": False},
                {"descricao": "Não agir",                             "nivel_mitigacao": "nenhuma","agrava": True},
            ]
        },
        {
            "nome"               : "Erro no software de navegação",
            "categoria"          : "Programming",
            "severidade"         : 4,
            "atributos_afetados" : ["fuel", "signal"],
            "impacto_base"       : 2.0,
            "probabilidade_base" : 0.25,
            "fases_ativas"       : ["launch", "transit", "operation", "return"],
            "peso_por_fase"      : {"launch": 2.0, "transit": 1.5, "operation": 1.0, "return": 1.5},
            "ticks_para_resolver": 3,
            "opcoes_resposta"    : [
                {"descricao": "Reiniciar sistema de navegação",   "nivel_mitigacao": "alta",   "agrava": False},
                {"descricao": "Aplicar patch manual",             "nivel_mitigacao": "media",  "agrava": False},
                {"descricao": "Não agir",                        "nivel_mitigacao": "nenhuma","agrava": False},
            ]
        },
        {
            "nome"               : "Falha no sistema de telemetria",
            "categoria"          : "Programming",
            "severidade"         : 2,
            "atributos_afetados" : ["signal"],
            "impacto_base"       : 2.0,
            "probabilidade_base" : 0.20,
            "fases_ativas"       : ["launch", "transit", "operation", "return"],
            "peso_por_fase"      : {"launch": 1.0, "transit": 1.0, "operation": 2.0, "return": 1.0},
            "ticks_para_resolver": 2,
            "opcoes_resposta"    : [
                {"descricao": "Reiniciar módulo de telemetria",   "nivel_mitigacao": "alta",   "agrava": False},
                {"descricao": "Alternar para canal secundário",   "nivel_mitigacao": "media",  "agrava": False},
                {"descricao": "Não agir",                        "nivel_mitigacao": "nenhuma","agrava": False},
            ]
        },
        {
            "nome": "Falha no reator nuclear",
            "categoria": "Power",
            "severidade": 5,
            "atributos_afetados": ["battery"],
            "impacto_base": 3.0,
            "probabilidade_base": 0.10,
            "fases_ativas": ["transit", "operation", "return"],
            "peso_por_fase": {"transit": 1.0, "operation": 1.5, "return": 1.5},
            "ticks_para_resolver": 6,
            "desativa_nuclear": True,
            "opcoes_resposta": [
                {"descricao": "Ativar reator de backup", "nivel_mitigacao": "alta", "agrava": False},
                {"descricao": "Reduzir consumo ao modo emergência", "nivel_mitigacao": "media", "agrava": False},
                {"descricao": "Não agir", "nivel_mitigacao": "nenhuma", "agrava": True},
            ]
        },
    ]