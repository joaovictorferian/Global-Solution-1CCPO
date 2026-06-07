from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mission-control-ai'
socketio = SocketIO(app, cors_allowed_origins="*")

resposta_usuario = {"valor": None, "evento": threading.Event()}

DESTINOS = {
    "1": ("LEO",   {"transito": 24,   "operacao": 48,   "retorno": 24}),
    "2": ("Lua",   {"transito": 72,   "operacao": 48,   "retorno": 72}),
    "3": ("Marte", {"transito": 5040, "operacao": 720,  "retorno": 5040}),
}


@app.route("/")
def index():
    return render_template("console.html")


@socketio.on("iniciar_missao")
def iniciar_missao(data):
    escolha = data.get("destino", "1")
    if escolha not in DESTINOS:
        emit("erro", {"msg": "Destino inválido."})
        return
    thread = threading.Thread(target=rodar_missao, args=(escolha,), daemon=True)
    thread.start()


@socketio.on("resposta_evento")
def receber_resposta(data):
    resposta_usuario["valor"] = data.get("escolha", 0)
    resposta_usuario["evento"].set()

def emitir_audio(nome):
    socketio.emit("tocar_audio", {"nome": nome}, namespace="/")


def emitir_telemetria(telemetry, fase, tick, horas_por_tick, extras=None):
    dados = {
        "fase": fase,
        "tick": tick,
        "tempo_h": tick * horas_por_tick,
        "battery": round(telemetry.battery, 1),
        "fuel": round(telemetry.fuel, 1),
        "signal": round(telemetry.signal, 1),
        "structural_integrity": round(telemetry.structural_integrity, 1),
        "radiation_exposure": round(telemetry.radiation_exposure, 1),
        "module_temp": round(getattr(telemetry, 'module_temp', 22.0), 1),
        "status": telemetry.status,
        "fator_solar": 1.0,
        "nuclear_ativa": False,
        "geracao_solar_kw": 0.0,
        "geracao_nuclear_kw": 0.0,
        "geracao_total_kw": 0.0,
        "consumo_total_kw": 0.0,
    }
    if extras:
        dados.update(extras)
        print(f"[DEBUG] Dados extras emitidos: {format(extras)}")
    print(f"[DEBUG] Emitindo: battery={dados['battery']} fuel={dados['fuel']} tick={dados['tick']} nuclear={dados['geracao_nuclear_kw']}")
    socketio.emit("telemetria", dados, namespace="/")
    time.sleep(0.05)


def emitir_evento(evento, opcoes):
    socketio.emit("evento_aleatorio", {
        "nome": evento["nome"],
        "categoria": evento["categoria"],
        "severidade": evento["severidade"],
        "atributos_afetados": evento["atributos_afetados"],
        "ticks_para_resolver": evento["ticks_para_resolver"],
        "opcoes": [{"descricao": o["descricao"]} for o in opcoes],
    }, namespace="/")


def emitir_ia(recomendacao):
    socketio.emit("recomendacao_ia", {"texto": recomendacao}, namespace="/")


def emitir_log(mensagem, tipo="info"):
    socketio.emit("log_entry", {"msg": mensagem, "tipo": tipo}, namespace="/")


def emitir_evento_resolvido(nome, recuperacao):
    socketio.emit("evento_resolvido", {
        "nome": nome,
        "recuperacao": round(recuperacao, 1),
    }, namespace="/")


def emitir_cascade(origem, destino, dano):
    socketio.emit("cascade", {
        "origem": origem,
        "destino": destino,
        "dano": round(dano, 1),
    }, namespace="/")

def emitir_contagem(valor):
    socketio.emit("contagem", {"valor": valor}, namespace="/")


def aguardar_resposta_usuario():
    resposta_usuario["evento"].clear()
    resposta_usuario["valor"] = None
    resposta_usuario["evento"].wait()
    return resposta_usuario["valor"]


def rodar_missao(escolha):
    from Telemetry import Telemetry
    from Launch import Launch
    from Transit import Transit
    from Operation import Operation
    from Return import Return
    from EventEngine import EventEngine
    from CascadeFailure import CascadeFailure

    nome, fases = DESTINOS[escolha]

    socketio.emit("missao_iniciada", {
        "destino": nome,
        "fases": fases,
    }, namespace="/")

    telemetry = Telemetry()
    cascade = CascadeFailure()

    callbacks = {
        "emitir_telemetria": emitir_telemetria,
        "emitir_evento": emitir_evento,
        "emitir_ia": emitir_ia,
        "emitir_log": emitir_log,
        "emitir_evento_resolvido": emitir_evento_resolvido,
        "emitir_cascade": emitir_cascade,
        "aguardar_resposta": aguardar_resposta_usuario,
        "emitir_contagem": emitir_contagem,
        "emitir_audio": emitir_audio
    }

    # FASE 1 — LANÇAMENTO
    socketio.emit("fase_iniciada", {"fase": "launch", "nome": "Lançamento"}, namespace="/")
    engine_launch = EventEngine(nome, "launch", cascade, callbacks)
    launch = Launch(telemetry, engine_launch, callbacks)
    telemetry = launch.run()

    time.sleep(1)

    # FASE 2 — TRÂNSITO
    socketio.emit("fase_iniciada", {"fase": "transit", "nome": "Trânsito"}, namespace="/")
    engine_transit = EventEngine(nome, "transit", cascade, callbacks)
    transit = Transit(telemetry, fases["transito"], nome, engine_transit, callbacks)
    telemetry = transit.run()

    perfil_nave = transit.PERFIL_NAVE[nome]

    time.sleep(1)

    # FASE 3 — OPERAÇÃO
    socketio.emit("fase_iniciada", {"fase": "operation", "nome": "Operação"}, namespace="/")
    engine_operation = EventEngine(nome, "operation", cascade, callbacks)
    operation = Operation(telemetry, fases["operacao"], nome, perfil_nave, engine_operation, callbacks)
    telemetry = operation.run()

    time.sleep(1)

    # FASE 4 — RETORNO
    socketio.emit("fase_iniciada", {"fase": "return", "nome": "Retorno"}, namespace="/")
    engine_return = EventEngine(nome, "return", cascade, callbacks)
    retorno = Return(telemetry, fases["retorno"], nome, perfil_nave, engine_return, callbacks)
    telemetry = retorno.run()

    # RESULTADO FINAL
    socketio.emit("missao_finalizada", {
        "sucesso": telemetry.sucesso,
        "battery": round(telemetry.battery, 1),
        "fuel": round(telemetry.fuel, 1),
        "radiation": round(telemetry.radiation_exposure, 1),
        "status": telemetry.status,
        "log": telemetry.event_log,
    }, namespace="/")


if __name__ == "__main__":
    socketio.run(app, debug=False, port=5000, allow_unsafe_werkzeug=True)