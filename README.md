# Mission Control AI

Sistema de simulação e monitoramento de missões espaciais, desenvolvido como projeto integrador (Global Solution) do 1º semestre de Ciência da Computação da FIAP da turma 1CCPO

---

## O que o sistema faz

O usuário escolhe um destino (LEO, Lua ou Marte) e o sistema simula a missão completa em quatro fases: lançamento, trânsito, operação no destino e retorno à Terra.

Durante a simulação, o sistema monitora seis atributos da espaçonave em tempo real: bateria, combustível, sinal de comunicação, integridade estrutural, radiação acumulada e temperatura dos módulos. Eventos aleatórios (falhas de motor, perda de sinal, impacto de meteorito, entre outros) podem acontecer a qualquer momento, e o sistema pede ao tripulante que escolha uma ação corretiva. Uma IA consulta documentos técnicos e recomenda qual ação tomar antes da decisão.

Se um sistema falha, o dano pode se propagar para outros sistemas em cascata — uma falha de energia pode derrubar a comunicação, por exemplo.

A missão pode terminar com sucesso ou com falha, dependendo das decisões tomadas ao longo da viagem.

---

## Estrutura de arquivos

```
Global-Solution-1CCPO/
├── server.py              # Servidor Flask + WebSocket (ponto de entrada web)
├── Mission.py             # Ponto de entrada terminal (sem interface web)
├── Telemetry.py           # Classe de telemetria (objeto compartilhado entre fases)
├── Launch.py              # Fase 1 — Lançamento
├── Transit.py             # Fase 2 — Trânsito (contém PERFIL_NAVE)
├── Operation.py           # Fase 3 — Operação no destino
├── Return.py              # Fase 4 — Retorno à Terra
├── EventEngine.py         # Motor de eventos aleatórios
├── EventCatalog.py        # Catálogo dos 12 eventos possíveis
├── CascadeFailure.py      # Grafo de dependências entre subsistemas
├── AdvisorAI.py           # Cliente HTTP que consulta a IA no Colab
├── Dashboard.py           # Gráfico matplotlib (modo terminal)
├── templates/
│   └── console.html       # Interface web do console da nave
├── static/
│   └── audio/             # Arquivos de áudio (contagem, alertas)
├── docs/                  # PDFs de referência para o RAG
│   ├── purdue_failures.pdf
│   ├── nasa_mars_power.pdf
│   └── nasa_potencia.pdf
└── README.md
```

---

## Como rodar

### Pré-requisitos

- Python 3.10 ou superior
- pip

### Instalação

```bash
git clone <url-do-repositório>
cd Global-Solution-1CCPO
python -m pip install flask flask-socketio matplotlib pymupdf requests python-dotenv
ou
py -m pip install flask flask-socketio matplotlib pymupdf requests python-doten
```

### Modo web (interface visual)

```bash
python server.py
```

Acesse `http://localhost:5000` no navegador. Escolha o destino e acompanhe a missão em tempo real.

### Modo terminal

```bash
python Mission.py
```

A simulação roda no terminal com prints formatados e gráfico matplotlib ao final.

### IA (opcional)

A IA roda em um notebook Google Colab separado. Para ativá-la:

1. Abra o notebook `IA Consultora.ipynb` no Google Colab
2. Execute todas as células (instala Ollama, carrega PDFs, cria vector store, inicia servidor Flask + ngrok)
3. Copie a URL do ngrok gerada (ex: `https://seu-dominio.ngrok-free.app`)
4. Cole a URL na variável `URL_COLAB` do arquivo `AdvisorAI.py`
5. Rode o projeto normalmente — a IA recomenda ações quando eventos acontecem

Se o Colab não estiver rodando, o projeto funciona normalmente sem a IA — o usuário escolhe a ação sozinho (Por isso classificamos ela como opcional).

---

## Arquitetura do sistema

### Fluxo da simulação

```
main.py / server.py
  └→ cria Telemetry (objeto compartilhado)
  └→ cria CascadeFailure (grafo de dependências)
  └→ para cada fase:
       └→ cria EventEngine (com catálogo de eventos + cascade)
       └→ cria a fase (Launch/Transit/Operation/Return)
       └→ fase.run() executa o loop de ticks
            └→ _update()          → atualiza telemetria
            └→ sortear_evento()   → sorteia evento aleatório
            └→ processar_ativos() → aplica dano contínuo + resolve
            └→ _check_alerts()    → verifica limites críticos
            └→ _print_status()    → imprime/emite status
       └→ retorna telemetry para a próxima fase
```

### Telemetry

Objeto central que todas as fases leem e escrevem. Atributos:

| Atributo | Unidade | Descrição |
|---|---|---|
| `battery` | % (de 200 kWh) | Nível de carga da bateria |
| `fuel` | % | Combustível restante |
| `signal` | dBm (negativo) | Potência do sinal recebido na Terra |
| `structural_integrity` | % | Integridade da estrutura |
| `radiation_exposure` | mSv | Radiação acumulada |
| `module_temp` | °C | Temperatura interna dos módulos |
| `status` | string | nominal, warning ou critical |
| `sucesso` | bool | Se a missão foi concluída com sucesso |

### Perfis de nave por destino

Definidos em `Transit.PERFIL_NAVE`:

| Parâmetro | LEO | Lua | Marte |
|---|---|---|---|
| Distância | 400 km | 384.400 km | 250.000.000 km |
| Frequência | 437 MHz (UHF) | 2.295 MHz (S-band) | 8.415 MHz (X-band) |
| EIRP | 30 dBm | 60 dBm | 90 dBm |
| Geração solar | 2,2 kW | 2,2 kW | 2,2 kW |
| Geração nuclear | 0 | 0 | 90 kW |
| Consumo base | 1,5 kW | 1,5 kW | 3,0 kW |
| Consumo comms | 0,2 kW | 0,5 kW | 1,0 kW |

---

## Modelo de energia

### Fórmula do balanço energético

```
geração_total = geração_solar + geração_nuclear
saldo = geração_total - consumo_total
variação_bateria(%) = (saldo_kW × dt_horas / capacidade_bateria_kWh) × 100
```

A capacidade da bateria é 200 kWh (referência: módulo da ISS).

### Energia solar

A geração solar varia com a distância ao Sol pela lei do inverso do quadrado:

```
fator_solar = (distância_sol_terra / distância_sol_atual)²
```

- LEO: fator ≈ 1.00 (sem degradação significativa)
- Lua: fator ≈ 0.99
- Marte: fator ≈ 0.43 (recebe 43% da irradiância terrestre)

Referência: NASA Mars Surface Power Technology Decision (2024).

### Energia nuclear

Ativada automaticamente quando a distância ao Sol ultrapassa 152.000.000 km (2M km além da órbita terrestre). Gera entre 80 e 100 kW com variação estocástica de ±5%.

Referência: NASA selecionou fissão nuclear como tecnologia primária de energia para missões tripuladas a Marte, com potência mínima de 10 kW para missões curtas e até centenas de kW para missões complexas.

### Sinal de comunicação (FSPL)

O sinal é calculado pelo modelo de perda no espaço livre (Free-Space Path Loss):

```
FSPL(dB) = 20 × log₁₀(distância_km) + 20 × log₁₀(frequência_MHz) + 32.44
Rx(dBm) = Tx(dBm) - FSPL + ruído_aleatório
```

O sinal é armazenado em dBm (valor negativo) — não em percentual.

### Temperatura dos módulos

Modelo de convergência térmica:

```
temp_alvo = temp_base(-40°C) + aquecimento_solar + calor_dos_sistemas
module_temp += (temp_alvo - module_temp) × 0.01 × dt
```

A temperatura converge gradualmente ao alvo — nunca muda instantaneamente.

---

## Eventos aleatórios

### Mecânica

A cada X ticks (10 para LEO/Lua, 5 para Marte), o EventEngine sorteia se um evento ocorre (30% de chance por sorteio). Se ocorrer, escolhe um evento do catálogo com probabilidade ponderada pela fase atual.

### Catálogo de eventos

12 eventos em 6 categorias, baseados na análise de falhas da Purdue University (Kattakuri, 2019):

| Categoria | Eventos | Subsistema afetado |
|---|---|---|
| Engine | Falha no motor principal, Vazamento de propelente | fuel |
| Power | Falha no painel solar, Sobrecarga elétrica, Falha no reator nuclear | battery |
| Communication | Perda de sinal, Interferência eletromagnética | signal |
| Structures | Micro-impacto de meteorito, Fadiga estrutural | structural_integrity |
| AD&C | Falha no controle de atitude | signal + fuel |
| Programming | Erro no software de navegação, Falha no sistema de telemetria | fuel + signal |

### Mitigação

Cada evento apresenta três opções de resposta com faixas de mitigação:

| Nível | Faixa de redução do impacto |
|---|---|
| Alta | 55% a 85% do dano é recuperado |
| Média | 25% a 50% do dano é recuperado |
| Nenhuma (omissão) | 0% ou agravamento de 10% a 30% |

Os valores são sorteados dentro da faixa a cada evento — a mesma ação pode resolver melhor ou pior em situações diferentes.

### Tempo de resolução

Cada ação leva de 2 a 6 ticks para ser executada. Durante esse tempo, a nave continua sofrendo dano proporcional. Múltiplos eventos podem acumular na fila simultaneamente.

---

## Cascade failure

Grafo direcionado de dependências entre subsistemas:

```
battery ──→ signal (faixa: 20-40% do dano)
battery ──→ fuel   (faixa: 20-40% do dano)
structural_integrity ──→ battery (faixa: 15-35%)
structural_integrity ──→ signal  (faixa: 15-35%)
```

Quando um subsistema sofre dano, o cascade propaga uma fração aleatória para os dependentes. A propagação pode encadear (A → B → C), com o dano diminuindo a cada nível.

Um set de `sistemas_afetados` impede loops infinitos na propagação.

---

## Inteligência Artificial

### Arquitetura RAG (Retrieval-Augmented Generation)

*É necessário utilizar a GPU T4 no ambiente de execução do Colab para melhor execução*

```
Evento acontece
  → EventEngine monta query de busca
  → ChromaDB busca os 2 chunks mais relevantes dos documentos
  → Chunks + dados do evento são enviados ao Ollama (llama3.1:8b)
  → Ollama recomenda uma das opções disponíveis
  → Recomendação é exibida ao usuário
  → Usuário decide se segue ou não
```

### Documentos do RAG

- Purdue University — "Failures in Spacecraft Systems: An Analysis from the Perspective of Decision Making" (Kattakuri, 2019): categorias de falha, causas raiz, fatores contribuintes
- NASA — "Mars Surface Power Technology Decision" (2024): decisão de fissão nuclear para Marte
- NASA — Capítulo 3.0 "Potência" (Small Spacecraft Technology State of the Art): células solares, baterias, PMAD

### Stack

- Ollama (llama3.1:8b) para geração de texto — roda no Google Colab
- ChromaDB como vector store — roda no Colab
- nomic-embed-text para embeddings
- Flask + ngrok expõe o servidor do Colab
- Código local faz requisição HTTP via `AdvisorAI.py`
- Acelerador de Hardware GPU T4 no ambiente de execução do Google Colab

---

## Interface web

### Tecnologias

- Flask para servir a página
- Flask-SocketIO para comunicação em tempo real via WebSocket
- HTML/CSS/JS vanilla no frontend (sem frameworks)

### Layout

O console simula o painel de controle de uma espaçonave:

- Topo: destino, fase atual, tempo de missão e tick
- Painel esquerdo: bateria, combustível, sinal e temperatura com barras e badges de status
- Painel central: console de eventos com opções de resposta, recomendação da IA e log
- Painel direito: radiação, integridade estrutural, energia solar, energia nuclear e balanço energético

### Comunicação

O servidor Python emite eventos via SocketIO a cada tick. O frontend escuta esses eventos e atualiza os valores dos atributos em tempo real. Quando um evento aleatório ocorre, a simulação pausa e espera o usuário escolher uma ação pelo navegador.

---

## Fontes e referências

- Kattakuri, V.R. (2019). *Failures in Spacecraft Systems: An Analysis from the Perspective of Decision Making*. MSME Thesis, Purdue University. Tabelas 3.1–3.4 (categorias de falha, probabilidades, causas raiz, fatores contribuintes) e Capítulo 4 (modelagem EPS com eficiências de células solares).
- NASA (2024). *Mars Surface Power Technology Decision*. 2024 Moon to Mars Architecture Concept Review. Seleção de fissão nuclear como tecnologia primária para missões tripuladas a Marte.
- NASA (2026). *Small Spacecraft Technology State of the Art — Chapter 3.0: Power*. Dados de células solares (Tabela 3-1), baterias (Tabela 3-4), sistemas PMAD (Tabela 3-8).
- Hundman et al. (2018). *Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding*. KDD 2018. Dataset SMAP/MSL de telemetria com anomalias rotuladas (referência para arquitetura RAG).
- Work of the US Gov. (August 1, 1996) * NASA NTRS - Spacecraft System Failures and Anomalies Attributed to the Natural Space Environment*
---

## Integrantes

| Nome | RM |
|---|---|
|João Victor Canello Ferian | 573295 |
|João Pedro Costenari | 572260 |
|Gustavo Melo dos Santos | 573562 |
