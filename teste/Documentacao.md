## 💻 1. Análise Funcional do Script de Carga (`locustfile.py`)

O script de teste de carga (`locustfile.py`) é a ferramenta fundamental para simular o comportamento real dos usuários na nossa aplicação de chat. Ele foi desenhado para gerar carga no **Módulo P (WEB API/Gateway)**, que é o ponto de entrada das requisições, simulando assim a **interação colaborativa** com os Módulos A e B, conforme a arquitetura distribuída.

O script simula uma sessão de chat completa, incluindo três tipos de carga distintos:

---

### Estrutura Funcional e Tipos de Carga Simulada

| Seção | Frequência/Carga | Contexto e Função no Teste |
| :--- | :--- | :--- |
| **Conexão Inicial** | Ocorre uma vez por usuário virtual. | Simula o ato do usuário **entrar no chat** (como 'Pedro' entrar na sala 'teste'). Essa ação estabelece a conexão WebSocket e aciona o **Módulo A (UserService gRPC)** para registrar o usuário. Mede a latência de login e estabelecimento da sessão. |
| **Envio de Mensagem** | **Alta Frequência (80% da carga)**. | Simula o envio de uma mensagem de texto (Carga Média). Essa é a operação mais comum do chat e testa a performance do **Módulo A (ChatService gRPC)** e a eficiência do *fan-out* das mensagens pelo Módulo P. |
| **Upload de Arquivo** | **Baixa Frequência (20% da carga)** e **Carga Pesada**. | Simula o envio de um arquivo de 10KB. Esta operação envolve dois passos: o *upload* de dados (Carga Pesada) via HTTP para o Módulo P, que aciona o **Módulo B (FileService gRPC)** para armazenamento, e a subsequente notificação via WebSocket. Mede a latência em operações de I/O intensivas. |

### Contexto de Observabilidade

Ao executar o teste com esse script realista, monitoramos a latência e o RPS para cada uma das três operações. Essa granularidade é essencial para identificar, através do Prometheus/Grafana, qual módulo (P, A ou B) se torna o **gargalo** (por exemplo, alta CPU no Módulo B em testes de Upload), permitindo direcionar as otimizações no Kubernetes com precisão.

---

## 📈 Metodologia para Garantir Observabilidade e Desempenho

A metodologia adotada neste projeto visa identificar o arranjo ideal da aplicação baseada em microserviços gRPC no cluster Kubernetes (K8S) em modo *cluster*, buscando otimizar a **performance** e a **elasticidade**. Para isso, realizamos testes comparativos de carga focados na métrica de desempenho.

### Ferramentas e Ambiente Adotados

* **Arquitetura:** Aplicação de chat em tempo real baseada em microserviços **gRPC** (Módulos P, A, B) com o **Módulo P** atuando como **Gateway WebSocket/WEB API**.
* **Cluster K8S:** Estruturado com um Nó Mestre e, pelo menos, dois Worker Nodes, incluindo recursos de autoscaling.
* **Teste de Carga:** Adotamos o **Locust** para simular usuários concorrentes, utilizando um *script* que simula o comportamento realista do chat (Conexão, Envio de Texto e Upload).
* **Monitoramento e Observabilidade:** O **Prometheus** foi instalado no K8S para coletar métricas do ambiente e da aplicação (CPU, Memória, Latência Interna) e o Grafana para a visualização dessas métricas.

### 1. Análise do Cenário A: Identificação do Limite (Stress Test)

O objetivo desta fase foi determinar o limite operacional da **Configuração Base** (1 réplica para P, A e B). Aumentamos o número de usuários ativos progressivamente (de 100 a 100.000 usuários) para identificar o ponto de saturação.

* **Foco da Análise:** Os testes revelaram que o principal gargalo não é o envio de mensagens (latência do `/ws/chat/send_text` permaneceu em $0.01 \text{ ms}$ mesmo sob extrema carga), mas sim a **capacidade de estabelecer novas conexões**.
* **Ponto de Degradação:** A latência média (`Average (ms)`) para estabelecer a conexão (`/ws/chat/connect`) aumentou significativamente a partir de **2.000 usuários**, atingindo $69.57 \text{ ms}$ e, posteriormente, **$124.56 \text{ ms}$ com 100.000 usuários**.
* **Identificação do Limite:** O sistema atinge o limite de *throughput* para mensagens em torno de **$290.9 \text{ RPS}$ com 5.000 usuários**. A partir de 100.000 usuários, o RPS de mensagens cai drasticamente para $0.5 \text{ RPS}$ devido à falha massiva no estabelecimento da conexão.
* **Conclusão:** O limite de **elasticidade da Conexão** (Handshake WebSocket) do Módulo P é o principal fator limitante do sistema na configuração atual.

### 2. Cenário B: Configuração Base (Baseline)

Com base nos resultados da Fase 1, estabelecemos a performance de referência (Baseline).

* **Configuração:** Aplicação instanciada num cenário simples (1 réplica para P, A e B).
* **Carga Adotada:** Utilizaremos uma carga de **2.000 usuários (50 *ramp up*)** como Baseline, pois este é o ponto onde o sistema ainda sustenta um alto RPS ($122.2 \text{ RPS}$) e a latência de conexão, embora elevada ($69.57 \text{ ms}$), ainda é considerada aceitável para testes comparativos.
* **Valores do Baseline (Requisitos do Trabalho):**
    * **Tempo médio para atender uma requisição (Conexão):** $\approx 69.57 \text{ ms}$.
    * **Máxima quantidade de RPS sustentável (Agregado):** $\approx 122.2 \text{ RPS}$.

### 3. Cenário C: Cenários Variáveis (Performance e Elasticidade)

Nesta fase, introduzimos variações no K8S, mantendo a carga estável de **2.000 usuários** (Baseline) para isolar o impacto da mudança no desempenho.

* **Variação de Elasticidade (HPA):** Ativaremos o **Horizontal Pod Autoscaler (HPA)** no **Módulo P** (Gateway) para verificar se o K8S escala automaticamente novas réplicas de P em resposta à alta CPU/Latência de Conexão, resultando em uma **diminuição na latência média** do `/ws/chat/connect` e estabilizando o RPS.
* **Variação de Réplicas (Performance):** Aumentaremos as réplicas dos **Módulos A e B** para comprovar se os servidores gRPC estavam atuando como um gargalo de processamento.
* **Conclusão:** Para cada cenário, o desempenho será cruzado com o monitoramento do Prometheus para determinar a configuração mais eficiente para garantir tanto a alta performance quanto a elasticidade do serviço de chat.

---

## 🚀 Passo a Passo: Instalação e Execução do Locust (Para Outros Membros)

Este passo a passo detalha a instalação e execução do Locust no ambiente Linux, assumindo que o Python 3 e o `pip` estão instalados.

### 1. Pré-requisitos (Instalação das Ferramentas)

A primeira etapa é instalar as bibliotecas necessárias para rodar o Locust e lidar com as conexões WebSocket.

```bash
# 1. Instala o Locust e as bibliotecas WebSocket (gevent-websocket e websocket-client)
pip install locust gevent-websocket websocket-client