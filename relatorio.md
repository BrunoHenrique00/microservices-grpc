# Relatório: Estratégias de Monitoramento e Observabilidade em Microsserviços Kubernetes

## Dados do Curso e Identificação dos Alunos

- **Alunos Participantes:**

  - Bruno Henrique Cardoso - 190134275
  - Guilherme Dib França - 190108088
  - João Gabriel Elvas - 190109599
  - Pedro Henrique Nogueira - 190094478

- **Disciplina:** Projeto de Sistemas Paralelos e Distribuídos (PSPD)
- **Data de Entrega:** dezembro de 2025
- **Instituição:** Universidade de Brasília (UnB)

---

## Introdução

Este relatório apresenta o desenvolvimento de estratégias de monitoramento e observabilidade em uma aplicação distribuída baseada em microserviços gRPC, executada em um ambiente Kubernetes em modo cluster. O trabalho estende a aplicação previamente desenvolvida, incorporando ferramentas de monitoramento, testes de carga e análise de elasticidade.

O objetivo central é explorar como as métricas de desempenho e a observabilidade através do Prometheus podem guiar decisões arquiteturais em ambientes containerizados, permitindo compreender o comportamento da aplicação sob diferentes cenários de carga e configurações de réplicas.

---

## 1. Metodologia e Organização do Projeto

### 1.1 Organização do Grupo

O projeto foi desenvolvido por um grupo de 4 alunos, com distribuição de responsabilidades entre as fases de:

- **Preparação e Configuração:** Definição da infraestrutura Kubernetes, setup do Docker Compose e deployments iniciais
- **Monitoramento:** Instalação e configuração do Prometheus, Grafana, Loki e Promtail
- **Testes:** Implementação e execução de cenários de carga com Locust
- **Documentação:** Coleta e análise de resultados, integração de dashboards

### 1.2 Roteiro de Encontros e Metodologia

O projeto seguiu uma metodologia iterativa com sprints semanais:

1. **Fase 1 - Setup Inicial:** Preparação do ambiente Docker Compose com os três módulos (P, A, B) funcionando localmente
2. **Fase 2 - Integração de Monitoramento:** Configuração do Prometheus para scrape de métricas dos módulos e setup inicial do Grafana
3. **Fase 3 - Desenvolvimento de Dashboards:** Criação de dashboards estratégicos para visualização de métricas HTTP, WebSocket e infraestrutura
4. **Fase 4 - Testes de Carga:** Execução de testes de estresse com Locust e coleta de dados de performance
5. **Fase 5 - Documentação:** Consolidação de resultados e lições aprendidas

## 2. Framework gRPC

O **gRPC** é um framework de comunicação remota de alto desempenho, criado pela Google, que utiliza o protocolo HTTP/2 e serialização de dados via Protocol Buffers (protobuf). Seus principais elementos são:

- **Protocol Buffers (protobuf):** Linguagem de definição de interface (IDL) que permite descrever mensagens e serviços de forma eficiente e independente de linguagem.
- **HTTP/2:** Protocolo de transporte que oferece multiplexação de streams, compressão de cabeçalhos e comunicação bidirecional eficiente.

### 2.1 Tipos de Comunicação gRPC

O gRPC suporta quatro tipos principais de comunicação:

1. **Unary:** Cliente envia uma requisição e recebe uma resposta única.
2. **Server Streaming:** Cliente envia uma requisição e recebe múltiplas respostas do servidor.
3. **Client Streaming:** Cliente envia múltiplas requisições e recebe uma resposta única.
4. **Bidirectional Streaming:** Cliente e servidor trocam múltiplas mensagens em ambos os sentidos.

### 2.2 Implementação no Projeto

No projeto, implementamos e testamos:

- **Unary:** Módulo A (Node.js) recebe uma requisição e retorna uma resposta processada.
- **Server Streaming:** Módulo B (Node.js) recebe uma requisição e retorna múltiplas respostas em sequência.

Os testes podem ser realizados via scripts em `examples/python/` ou via frontend, selecionando o tipo de operação desejada.

---

## 3. Montagem do Cluster Kubernetes

### 3.1 Arquitetura e Configuração

O cluster Kubernetes foi estruturado conforme requisitos com:

- **Nó Master (Control Plane):** Gerencia o cluster, API Server, etcd, controller-manager, scheduler
- **Nós Worker:** Mínimo de 2 nós para execução de pods
- **Networking:** Configuração de descoberta de serviços interna e exposição externa
- **Storage:** Volumes persistentes para Prometheus e dados de aplicação

### 3.2 Ferramentas e Passos de Instalação

**Ferramentas Utilizadas:**

- Docker e Docker Compose para orquestração local
- Minikube para simulação de cluster Kubernetes
- kubectl para gerenciamento do cluster

**Passos de Instalação:**

1. Instalação dos componentes do Kubernetes (via Minikube)
2. Configuração da rede (CNI plugin - Weave/Flannel)
3. Inicialização do cluster com `minikube start`
4. Configuração do Docker para acessar o registry do Minikube
5. Build e deploy das imagens dos módulos
6. Validação da arquitetura com `kubectl get pods` e `kubectl get services`

### 3.3 Interface Web de Monitoramento

O cluster Kubernetes foi configurado com:

- **Kubernetes Dashboard:** Acesso via `minikube dashboard` para visualização de pods, deployments, services e recursos
- **Prometheus UI:** Disponível em `http://localhost:9090`
- **Grafana Dashboard:** Interface web em `http://localhost:3000` para visualização de métricas customizadas

### 3.4 Dificuldades Encontradas

**Desafios na Implantação:**

1. **Integração de Monitoramento:** Principal dificuldade foi configurar o Prometheus para scrape de métricas de Node.js (Módulos A e B) e FastAPI (Módulo P) no Docker Compose, exigindo exposição de portas específicas (5001, 5002)

2. **Sincronização de Builds:** Garantir sincronização correta entre ambiente local e Minikube, resolvido com ajustes em variáveis de ambiente

3. **Descoberta de Serviços:** Configuração de nomes de serviço DNS do Kubernetes para comunicação gRPC entre módulos

---

## 4. Monitoramento com Prometheus

### 4.1 Configuração do Prometheus

O Prometheus foi instalado no cluster para coletar métricas de desempenho da aplicação:

- **Scrape Targets:**

  - Módulo P: porta 8000 (`/metrics`)
  - Módulo A: porta 5001 (`/metrics`)
  - Módulo B: porta 5002 (`/metrics`)

- **Interval de Coleta:** 15 segundos
- **Persistência:** Volume Docker em `docker-compose.yml`
- **Retention Policy:** 30 dias de retenção

**Arquivo:** `docker-monitoring/prometheus/prometheus.yml`

### 4.2 Métricas Coletadas

As principais métricas monitoradas foram:

**Módulo P (FastAPI/WebSocket):**

- Requisições por Segundo (RPS) HTTP e WebSocket
- Duração Média de Requisições
- Taxa de Sucesso (2xx) e Erro (5xx) - Resultado: Taxa de erro 28.1% sob carga
- Conexões WebSocket Ativas
- Latência: P50, P95, P99

**Módulos A e B (Node.js/gRPC):**

- Uso de CPU do Processo (%)
- Uso de Memória (Heap, Externo, Total)
- Requisições/Handlers Ativos
- Event Loop Lag
- Taxa de Erro gRPC

### 4.3 Interface de Visualização (Grafana)

**Stack de Monitoramento Completo:**

- **Prometheus:** Armazenamento de séries temporais de métricas
- **Grafana:** Visualização e dashboarding de métricas
- **Loki:** Agregação de logs estruturados
- **Promtail:** Coleta de logs dos containers

**Dashboards Criados:**

1. **Dashboard do Módulo P:** Gráficos de RPS, taxa de erro, latência, conexões WebSocket ativas
2. **Dashboard de Infraestrutura A/B:** CPU Usage, Memory Usage, Event Loop Lag, Requests/segundo
3. **Dashboard de Logs:** Agregação de logs de todos os módulos com filtros por severidade

**Arquivos:** `docker-monitoring/grafana/provisioning/dashboards/`

---

## 5. Aplicação Base

### 5.1 Descrição da Arquitetura

A aplicação segue a arquitetura de três módulos interconectados:

```
Frontend (HTTP) → Módulo P (FastAPI/Gateway) → gRPC → Módulo A → gRPC → Módulo B
```

#### Módulo P (Gateway HTTP → gRPC)

- **Linguagem:** Python com FastAPI
- **Porta:** 8000 (HTTP)
- **Responsabilidades:**
  - Receber requisições REST do frontend
  - Converter para chamadas gRPC
  - Orquestrar chamadas aos servidores A e B
  - Coletar métricas de latência

#### Módulo A (Servidor gRPC - Unary)

- **Linguagem:** Node.js
- **Porta gRPC:** 50051
- **Operações:** uppercase, lowercase, reverse, length
- **Tipo de Chamada:** Unary (1 req → 1 resp)

#### Módulo B (Servidor gRPC - Streaming)

- **Linguagem:** Node.js
- **Porta gRPC:** 50052
- **Tipo de Chamada:** Server Streaming (1 req → N resps)
- **Recurso:** Múltiplas respostas em sequência

### 5.2 Instrumentação de Métricas

Os módulos foram instrumentados para expor métricas ao Prometheus:

**Módulo P (FastAPI/Python):**

- Bibliotecas: `prometheus-fastapi-instrumentator`, `prometheus_client`
- Métricas customizadas para WebSocket: contador de conexões/desconexões, gauge de conexões ativas, histogramas de latência
- Endpoint: `/metrics` (porta 8000)

**Módulo A (Node.js/gRPC):**

- Biblioteca: `prom-client`
- Arquivo: `metrics.js`
- Métricas: contador de mensagens processadas, duração de processamento, moderações ativas, palavras bloqueadas
- Endpoint: `/metrics` (porta 5001)

**Módulo B (Node.js/gRPC):**

- Biblioteca: `prom-client`
- Métricas: contador de arquivos processados, tamanho total de cache, tempo de upload/download
- Endpoint: `/metrics` (porta 5002)

Todas as métricas são coletadas a cada 15 segundos pelo Prometheus.

---

## 6. Cenários de Teste e Resultados

### 6.1 Ferramenta de Teste de Carga

**Ferramenta Escolhida:** Locust

**Arquivo:** `teste/locustfile.py`

**Configuração:**

- **Usuários simultâneos:** 1000 usuários
- **Taxa de spawn:** 150 usuários por segundo
- **Duração:** 5-10 minutos
- **Endpoints testados:** Login, envio de mensagens, upload de arquivos, WebSocket

**Comportamento dos Usuários Virtuais:**

1. Fazer login no sistema
2. Conectar via WebSocket à sala de chat
3. Enviar mensagens em intervalos aleatórios
4. Upload de arquivos simulados
5. Manter conexão ativa durante o teste

### 6.2 Cenários Variáveis

#### Cenário 1: Aumento de Réplicas (Módulo P)

**Configuração:**

- Réplicas: 3 para Módulo P (Gateway)
- Réplicas: 1 para Módulos A e B
- Usuários: 1000
- Taxa de ramp: 100/s

**Resultados Esperados:**

| Métrica          | Cenário Base | Cenário 1 | Melhoria Esperada |
| ---------------- | ------------ | --------- | ----------------- |
| Tempo Médio (ms) | 6.68         | ~3-4      | ~50-60%           |
| RPS Máximo       | 333.1        | ~600-800  | ~80-140%          |
| Taxa de Erro (%) | 100% (login) | ~20-30%   | ~70-80%           |
| CPU Média (%)    | 1.79         | ~3-5      | Moderado aumento  |

**Análise:**

Com 3 réplicas do Módulo P, esperamos que o gateway distribua melhor a carga entre os 3 pods. Isso deveria permitir que mais requisições de login sejam processadas simultaneamente, reduzindo o gargalo identificado no cenário base. A taxa de erro deve cair significativamente, embora pode não chegar a zero se o gargalo estiver no Módulo A.

#### Cenário 2: Carga Intensiva 2000 Usuários

**Configuração:**

- Usuários: 2000 (2x da baseline)
- Taxa de ramp: 150/s (vs 100/s)
- Réplicas: 1 para cada módulo (baseline)
- Duração: 300s

**Resultados Observados:**

| Métrica             | 1000 Users | 2000 Users | Delta |
| ------------------- | ---------- | ---------- | ----- |
| Tempo Médio (ms)    | 6.68       | 11.24      | +68%  |
| RPS Máximo          | 333.1      | 669.4      | +101% |
| CPU Média (%)       | 1.79       | 3.58       | +100% |
| P95 Latência (ms)   | 41         | 66         | +61%  |
| P99 Latência (ms)   | 68         | 130        | +91%  |
| Login Latência (ms) | 44.1       | 63.63      | +44%  |

**Análise:**

Com 2000 usuários, a latência aumenta proporcionalmente (68%) enquanto RPS dobra (669.4). CPU dobra para 3.58%, indicando melhor utilização da infraestrutura mas ainda longe do limite. O gargalo permanece no login: ambas as cargas resultam em 100% de erro. Isso confirma que o problema não é falta de capacidade de processamento em geral, mas especificamente no módulo de autenticação/gateway.

#### Cenário 3: Carga Extrema 3000 Usuários

**Configuração:**

- Usuários: 3000 (3x da baseline)
- Taxa de ramp: 200/s (vs 100/s)
- Réplicas: 1 para cada módulo (baseline)
- Duração: 300s

**Resultados Observados:**

| Métrica             | 1000 Users | 3000 Users | Delta  |
| ------------------- | ---------- | ---------- | ------ |
| Tempo Médio (ms)    | 6.68       | 100.11     | +1400% |
| RPS Máximo          | 333.1      | 994.5      | +198%  |
| P95 Latência (ms)   | 41         | 1100       | +2585% |
| P99 Latência (ms)   | 68         | 1400       | +1959% |
| Login Latência (ms) | 44.1       | 1019.87    | +2212% |
| WebSocket Latência  | 15.28      | 281.06     | +1739% |

**Análise:**

Com 3000 usuários, o sistema entra em estado de degradação severa. Login latência explode para >1s (vs 44ms na baseline), e WebSocket latência para ~281ms. RPS alcança máximo de 994.5 (3x o baseline) mas com latências inaceitáveis (P95 ultrapassa 1100ms). Isso demonstra limite físico do sistema: não consegue processar >1000 requisições/s mantendo latência aceitável. O gargalo é crítico no gateway (Módulo P).

#### Cenário 4: Recomendações para Otimização

Baseado nos dados dos 3 testes realizados, as seguintes estratégias são recomendadas:

**1. Aumentar Réplicas do Módulo P (Gateway):**

- Teste com 1000 users mostrou 100% erro no login
- Distribuição entre 3+ réplicas deve reduzir latência de login em ~40-50%
- Esperado: reduzir taxa de erro para <50% com 3 réplicas

**2. Implementar Connection Pooling:**

- Módulo P (FastAPI) cria nova conexão gRPC para cada requisição
- Com pool de conexões reutilizáveis, overhead reduz significativamente
- Esperado: 20-30% melhoria em latência

**3. Adicionar Cache de Respostas:**

- Listagem de mensagens e usuários são operações read-only
- Cache Redis reduz carga no Módulo A
- Esperado: 50%+ redução em latência de GET requests

**4. Circuit Breaker e Rate Limiting:**

- Protege sistema de degradação em cascata
- Rejeita requisições gracefully quando sistema está saturado
- Esperado: melhoria de user experience (fail fast vs timeout longo)

**Prognóstico com Otimizações Aplicadas:**

| Otimização        | 1000 Users | 2000 Users | 3000 Users |
| ----------------- | ---------- | ---------- | ---------- |
| Apenas 3 réplicas | 6-8ms      | 12-15ms    | 40-60ms    |
| + Connection pool | 4-5ms      | 8-10ms     | 25-35ms    |
| + Cache           | 2-3ms      | 5-7ms      | 15-20ms    |
| + Circuit breaker | Estável    | Estável    | Degradado  |

**Conclusão:** Sistema atual suporta até ~500 RPS em produção com latência aceitável. Para suportar 1000+ RPS, necessário combinar múltiplas otimizações (réplicas + pool + cache).

### 6.3 Análise Comparativa

**Tabela Consolidada - Dados Reais:**

| Cenário               | Usuários | Latência Média (ms) | RPS Máximo | CPU (%) | P99 Latência (ms) |
| --------------------- | -------- | ------------------- | ---------- | ------- | ----------------- |
| Baseline (atual)      | 1000     | 6.68                | 333.1      | 1.79    | 68                |
| Carga 2x (2000 users) | 2000     | 11.24               | 669.4      | 3.58    | 130               |
| Carga 3x (3000 users) | 3000     | 100.11              | 994.5      | N/A     | 1400              |
| Projeção: 3 réplicas  | 1000     | ~3.5-4.0            | ~500-550   | ~3.2    | ~35-45            |

**Conclusões por Cenário:**

**Baseline (1000 users, 100 ramp/s):**

- ✓ Latência média aceitável (6.68ms)
- ✗ 100% erro no login (gargalo crítico)
- ✓ Endpoints GET excelentes (3-4ms)
- ✓ Infrastructure subutilizada (CPU 1.79%, Mem 62-69MB)
- **Recomendação:** Aumentar réplicas do Módulo P

**Carga Intensiva 2x (2000 users, 150 ramp/s):**

- Latência sobe 68% para 11.24ms
- RPS dobra para 669.4 (linear scaling)
- CPU dobra para 3.58% (ainda subutilizado)
- Taxa de erro continua 100% (não é falta de CPU)
- **Insight:** Gargalo é no Módulo P (gateway), não na infraestrutura

**Carga Extrema 3x (3000 users, 200 ramp/s):**

- Latência explode para 100.11ms (1400% aumento)
- P99 latência ultrapassa 1400ms (inaceitável)
- Login latência alcança 1019.87ms (vs 44.1ms baseline)
- RPS máximo 994.5 (limite físico do sistema)
- **Encontrado:** Limite máximo ~500-600 RPS em latência aceitável

**Projeção com 3 Réplicas do Módulo P:**

- Distribuição de carga entre 3 pods
- Esperado ~50% redução em latência
- Pode suportar 500-550 RPS com latência <10ms
- Mantém overhead baixo, sem overhead de HPA

---

## 7. Conclusão Geral

### 7.1 Principais Aprendizados

Este projeto demonstrou a importância crítica da observabilidade em ambientes distribuídos. Os principais aprendizados foram:

1. **Monitoramento ativo identificou gargalo específico:** Prometheus permitiu descobrir que o login é o gargalo crítico (100% erro) não por falta de recursos (CPU 1.79%, Mem 62-69MB) mas por arquitetura. Sem instrumentação granular por endpoint, seria impossível diagnosticar.

2. **Escalabilidade linear até limite:** O sistema escala linearmente: 2000 users = 2x RPS (669.4 vs 333.1), 3000 users = 3x RPS (994.5). Isso prova infraestrutura OK e problema é no Módulo P (gateway).

3. **Limite físico descoberto:** Sistema alcança ~1000 RPS máximo (3000 users) com latência inaceitável (100ms+). O limite aceitável é ~500 RPS (latência <10ms).

4. **Distribuição de carga essencial:** Ter um único pod de gateway é ponto único de falha. 3 réplicas devem reduzir latência ~50% e taxa de erro drasticamente.

5. **Análise de Endpoints revelou padrão crítico:**

   - Login: 44.1ms latência, 100% erro (gargalo crítico)
   - Mensagens: 3.74ms latência, 0% erro
   - Listagem: 4.04ms latência, 0% erro
   - Health: 3.63ms latência, 0% erro

   Indica que POST é mais custoso que GET, e login é particularmente caro.

6. **Comportamento previsível em estresse:** Com 3000 users, latência explode 1400% mas RPS ainda sobe 200% - o sistema não colapsa, apenas degrada gracefully.

### 7.2 Dificuldades Encontradas

**Desafios Técnicos Superados:**

1. **Integração de Monitoramento em Ambiente Heterogêneo:**

   - Problema: Configuração correta do Prometheus para scrape de métricas de múltiplas linguagens (Python, Node.js) em portas diferentes
   - Solução: Expor portas específicas (5001, 5002) para endpoints `/metrics` e configurar targets no `prometheus.yml`

2. **Gargalo Crítico no Gateway - Autenticação:**

   - Problema: 100% de erro no endpoint `/api/chat/login` com 1000+ usuários simultâneos
   - Causa Raiz: M\u00f3dulo P (FastAPI) n\u00e3o consegue processar spike de requisi\u00e7\u00f5es de autentica\u00e7\u00e3o. Cada requisi\u00e7\u00e3o cria nova conex\u00e3o gRPC para Módulos A/B, causando esgotamento.
   - Solução: Implementar connection pooling e aumentar réplicas do Módulo P para distribuir carga

3. **Comportamento de Degradação em Cascata:**

   - Problema: Quando login falha (100%), WebSocket connections também falham (100%), impedindo toda aplicação
   - Observação: RPS de outras operações (mensagens, health) continuam 100% disponíveis, confirmando isolamento de falha
   - Solução: Implementar circuit breaker para evitar timeouts longos quando serviço está degradado

4. **Escala não Linear de Latência:**

   - Problema: De 1000 para 3000 users, latência sobe 1400% (6.68 → 100.11ms) enquanto RPS sobe apenas 200%
   - Indicador: Sistema entra em contenção severa (fila de requisições cresce exponencialmente)
   - Solução: Definir limite de taxa (rate limiting) para rejeitar requests gracefully em vez de enfileirar

5. **Correlação entre Métricas Dispersas:**
   - Problema: Dados do Locust (RPS, latência) precisavam ser correlacionados com métricas Prometheus (CPU, memória)
   - Solução: Exportar timestamps sincronizados e criar dashboards unificadas no Grafana

---

## 8. Comentários Pessoais dos Alunos

### 8.1 Bruno Henrique Cardoso (190134275)

**Contribuições Principais:**

- Implementação do Módulo P (Gateway FastAPI/WebSocket)
- Integração de comunicação gRPC entre módulos
- Implementação de streaming bidirecional para transferência de arquivos
- Gerenciamento de conexões WebSocket com histórico persistente
- Recuperação automática de dados em client-server distribuído

**Aprendizados:**

- Reforçou o entendimento de arquiteturas de microsserviços
- Compreensão profunda de comunicação assíncrona com WebSocket
- Importância de um gateway eficiente para gerenciar diferentes protocolos
- Integração de múltiplas linguagens em um único projeto

**Autoavaliação:** 9/10

### 8.2 Guilherme Dib França (190108088)

**Contribuições Principais:**

- Implementação da integração e configuração do Prometheus e Grafana
- Exposição de métricas customizadas nos Módulos A, B e P
- Ajuste do `docker-compose.yml` para subir a stack de monitoramento
- Configuração de volumes persistentes e variáveis de ambiente
- Troubleshooting de conectividade entre serviços

**Aprendizados:**

- Aprofundamento em ferramentas de observabilidade (Prometheus/Grafana)
- Coleta de métricas em ambientes distribuídos heterogêneos
- Importância de visualizar a saúde da infraestrutura em tempo real
- Configuração de scrape targets e data sources

**Autoavaliação:** 9/10

### 8.3 João Gabriel Elvas (190109599)

**Contribuições Principais:**

- Desenvolvimento do Locust para teste de estresse
- Configuração e otimização dos dashboards no Grafana
- Integração do Loki/Promtail para agregação de logs
- Criação de queries PromQL para análise de performance
- Correlação de dados entre Locust e Prometheus

**Aprendizados:**

- Uso avançado do Locust para simular carga em diferentes endpoints
- Simulação de WebSocket connections em teste de carga
- Correlação de dados de estresse com métricas de desempenho
- Identificação de gargalos e limites da aplicação através de dados
- Criação de dashboards efetivos para diagnóstico rápido

**Autoavaliação:** 9/10

### 8.4 Pedro Henrique Nogueira (190094478)

**Contribuições Principais:**

- Desenvolvimento e execução dos testes de carga com Locust (`teste/locustfile.py`)
- Simulação de 1000, 2000 e 3000 usuários simultâneos
- Coleta e análise de métricas de performance (RPS, latência, taxa de erro)
- Identificação de gargalos no Módulo P (gateway)
- Correlação de resultados do Locust com métricas do Prometheus

**Aprendizados:**

- Diferença entre teoria e prática em ambientes distribuídos
- Importância da instrumentação desde o início do desenvolvimento
- Configuração externa e discovery de serviços em Docker
- Depuração de problemas em arquitetura distribuída
- Infraestrutura como código para gerenciar complexidade

**Autoavaliação:** 9/10

---

## 9. Referências

- Kubernetes Documentation: https://kubernetes.io/docs/
- Prometheus: Monitoring system & time series database: https://prometheus.io/
- gRPC: A high performance RPC framework: https://grpc.io/
- Docker Documentation: https://docs.docker.com/
- Grafana: Observability platform: https://grafana.com/
- Locust: Open source load testing tool: https://locust.io/
- CNCF Cloud Native Computing Foundation: https://www.cncf.io/

---

## Apêndice

### A. Definições de Interface gRPC

**Arquivo:** `protos/servico.proto`

### B. Scripts e Ferramentas

- **Teste de Carga:** `teste/locustfile.py`
- **Scripts de Deploy:** `start.sh`, `kubernetes_start.sh`
- **Configuração Prometheus:** `docker-monitoring/prometheus/prometheus.yml`
- **Dashboards Grafana:** `docker-monitoring/grafana/provisioning/dashboards/`

### C. Instruções de Execução

#### Com Docker Compose:

```bash
./start.sh
```

#### Com Kubernetes:

```bash
./kubernetes_start.sh
kubectl apply -f kubernetes/
```

#### Testes de Carga:

```bash
locust -f teste/locustfile.py -u [num_users] -r [spawn_rate] --headless
```

### D. Estrutura do Repositório

```
.
├── modulo_A/              # Servidor gRPC A (Node.js)
├── modulo_B/              # Servidor gRPC B (Node.js)
├── modulo_P/              # Gateway HTTP→gRPC (Python)
├── frontend/              # Interface web
├── kubernetes/            # Manifests K8S
├── docker-monitoring/     # Prometheus, Grafana, Promtail
├── teste/                 # Scripts de teste de carga
├── protos/                # Definições Protocol Buffers
├── docker-compose.yml     # Orquestração local
└── relatorio.md           # Este documento
```

---
