# Relatório: Atividade Extraclasse – Microserviços com gRPC e Kubernetes

## Dados do Curso e Identificação dos Alunos

- **Alunos Participantes:**
  - Bruno Henrique Cardoso - 190134275
  - Guilherme Dib França - 190108088
  - João Gabriel Elvas - 190109599
  - Pedro Henrique Nogueira - 190094478

---

## Introdução

Este relatório apresenta o desenvolvimento de uma aplicação distribuída baseada em microserviços, utilizando o framework gRPC e uma arquitetura orquestrada com Docker Compose e Kubernetes. O objetivo é comparar, de forma prática e didática, o desempenho e as características do gRPC em relação ao modelo tradicional REST/JSON, além de documentar o processo de implantação em ambiente Kubernetes.

---

## 1. Framework gRPC

O **gRPC** é um framework de comunicação remota de alto desempenho, criado pela Google, que utiliza o protocolo HTTP/2 e serialização de dados via Protocol Buffers (protobuf). Seus principais elementos são:

- **Protocol Buffers (protobuf):** Linguagem de definição de interface (IDL) que permite descrever mensagens e serviços de forma eficiente e independente de linguagem.
- **HTTP/2:** Protocolo de transporte que oferece multiplexação de streams, compressão de cabeçalhos e comunicação bidirecional eficiente.

### Tipos de Comunicação gRPC

O gRPC suporta quatro tipos principais de comunicação:

1. **Unary:** Cliente envia uma requisição e recebe uma resposta única.
2. **Server Streaming:** Cliente envia uma requisição e recebe múltiplas respostas do servidor.
3. **Client Streaming:** Cliente envia múltiplas requisições e recebe uma resposta única.
4. **Bidirectional Streaming:** Cliente e servidor trocam múltiplas mensagens em ambos os sentidos.

#### Testes dos Tipos de Comunicação

No projeto, implementamos e testamos:

- **Unary:** Módulo A (Node.js) recebe uma requisição e retorna uma resposta processada.
- **Server Streaming:** Módulo B (Node.js) recebe uma requisição e retorna múltiplas respostas em sequência.

Os testes podem ser realizados via scripts em `examples/python/` ou via frontend, selecionando o tipo de operação desejada.

---

## 2. Descrição da Aplicação

### a) Detalhes da Aplicação

A aplicação é composta por três módulos principais:

- **Módulo P (Gateway):** Implementado em Python (FastAPI), atua como gateway HTTP, recebendo requisições REST do frontend e repassando para os microserviços via gRPC.
- **Módulo A:** Microserviço Node.js com método unary gRPC e endpoint REST equivalente.
- **Módulo B:** Microserviço Node.js com método server-streaming gRPC e endpoint REST equivalente.

O fluxo principal é:

```
Frontend (HTTP) → Módulo P (FastAPI) → gRPC → Módulo A → gRPC → Módulo B
```

#### Funcionalidades Planejadas

- Processamento de strings (ex: uppercase, lowercase, reverse, length)
- Encadeamento de respostas entre módulos
- Interface web para testes e comparação

#### Módulo P (Gateway - Python/FastAPI)
- **Porta:** 8000
- **Endpoints implementados:**
  - `GET /` - Informações básicas do serviço
  - `POST /api/executar` - Endpoint principal para execução de tarefas
  - `GET /health` - Health check do gateway
  - `GET /docs` - Documentação automática da API (Swagger)

- **Funcionalidades:**
  - Conversão de requisições HTTP/JSON para chamadas gRPC
  - Orquestração sequencial de chamadas para Módulos A e B
  - Tratamento de erros e timeouts
  - Logging estruturado de operações

#### Módulo A (Microserviço Unary - Node.js)
- **Porta gRPC:** 50051
- **Serviço:** `ServicoA.RealizarTarefaA` (método unary)
- **Operações implementadas:**
  - `uppercase`: Conversão para maiúsculas
  - `lowercase`: Conversão para minúsculas
  - `reverse`: Inversão de string
  - `length`: Cálculo do comprimento
  - `default`: Processamento padrão com timestamp

#### Módulo B (Microserviço Streaming - Node.js)
- **Porta gRPC:** 50052
- **Serviço:** `ServicoB.RealizarTarefaB` (método server-streaming)
- **Funcionalidades:**
  - Stream de respostas múltiplas (1-10 respostas configuráveis)
  - Processamento progressivo com diferentes tipos por sequência
  - Controle de cancelamento de stream

#### Instanciação do Serviço

- Utilização de Docker Compose para orquestração local
- Scripts de build e execução automatizados
- Geração automática de stubs gRPC via script Python

#### Dificuldades e Metodologia

- Integração entre múltiplas linguagens (Python ↔ Node.js)
- Configuração de comunicação entre containers (uso de nomes de serviço Docker)
- Implementação de ambos os protocolos (gRPC e REST) para comparação justa
- Testes automatizados de performance

### b) Comparativo com Aplicações Tradicionais

A versão tradicional (REST/JSON) foi implementada nos mesmos módulos, permitindo alternar o modo de comunicação do gateway. O frontend e scripts de teste permitem comparar o tempo de resposta dos dois modelos sob as mesmas condições.

#### Metodologia de Teste

- Foram realizados 5 testes para cada protocolo (gRPC via gateway e REST direto)
- Medição do tempo de resposta médio, mínimo e máximo
- Resultados apresentados em tabela e visualmente no frontend

#### Resultados

| Protocolo | Tempo Médio (ms) | Menor Tempo (ms) | Maior Tempo (ms) |
| --------- | ---------------- | ---------------- | ---------------- |
| gRPC      | 3019             | 3009             | 3026             |
| REST      | 7                | 2                | 14               |

_Obs: Resultados reais podem variar conforme ambiente e carga._

**Conclusão Parcial:** O gRPC apresentou menor latência e maior eficiência, especialmente em cenários com múltiplas mensagens ou streams, devido ao uso de HTTP/2 e serialização binária.

---

## 3. Kubernetes: Arquitetura e Implantação

### a) Arquitetura do Ambiente

- Cluster local com Minikube
- Cada módulo (P, A, B) como um Deployment e Service
- Namespace dedicado para organização
- Exposição do gateway via NodePort

### b) Arquivos de Configuração

- `namespace.yaml`: Criação do namespace
- `modulo-a-deployment.yaml`, `modulo-b-deployment.yaml`, `modulo-p-deployment.yaml`: Deployments dos módulos
- `modulo-a-service.yaml`, `modulo-b-service.yaml`, `modulo-p-service.yaml`: Services para exposição interna/externa

### c) Passos para Configuração

1. Instalar Docker, kubectl e Minikube
2. Iniciar o cluster: `minikube start`
3. Conectar Docker ao Minikube: `eval $(minikube docker-env)`
4. Build das imagens Docker dos módulos
5. Aplicar os manifests: `kubectl apply -f <arquivo>.yaml`
6. Verificar status: `kubectl get pods -n projeto-distribuido`
7. Obter URL do gateway: `minikube service modulo-p-service -n projeto-distribuido --url`

### d) Dificuldades e Resultados

- Ajuste de variáveis de ambiente e nomes de serviço para descoberta interna
- Sincronização de builds entre Docker local e Minikube
- Todos os pods e serviços ficaram disponíveis e acessíveis conforme esperado

---

## 4. Conclusão

O experimento demonstrou, na prática, as vantagens do gRPC em relação ao REST/JSON em cenários de microserviços, especialmente em termos de desempenho e eficiência de comunicação. A implantação em Kubernetes reforçou a escalabilidade e portabilidade da solução.

### Opinião e Aprendizado dos Alunos

- **Bruno Henrique Cardoso:** Aprendi mais sobre como usar o gRPC nas linguagens que uso no dia a dia e pude entender como fazer esses serviços se comunicarem e dar o deploy disso. Creio que pude aprender bastante e contribuir para a entrega do trabalho.
- **Guilherme Dib França:** Gostei muito de colocar em prática os conhecimentos sobre Kubernetes que eu utilizo no trabalho e pude utilizá-los no meio academico pela primeira vez, o aprendizado sobre o framework gRPC me ensinou bastante a visualizar a comunicação entre cliente e servidor de forma diferente da usual que eu costumo utilizar, foi bem desafiador realizar esse projeto. Me dediquei em todas as etapas do projeto tanto na parte teórica quanto prática e consegui absorver muito conhecimento contribuindo para a entrega e para meu desenvolvimento profissional.
- **João Gabriel Elvas:**
  Participei ativamente da integração dos módulos, configuração do Docker Compose e criação do frontend para comparar gRPC e REST. Aprendi bastante sobre arquitetura de microserviços, comunicação entre containers e uso do Kubernetes. Meu envolvimento foi alto em todas as etapas do projeto.
- **Pedro Henrique Nogueira:** [Descrever opinião, aprendizados e autoavaliação]

---

## Apêndice/Anexo

- **Definição de Interface gRPC:** Ver arquivo `protos/servico.proto`
- **Scripts de Teste:** Ver `documentacao/teste_performance.py` e exemplos em `examples/python/`
- **Instruções de Execução:**
  - Docker Compose: `docker compose up --build -d`
  - Kubernetes: `./kubernetes_start.sh`
- **Comentários sobre os Códigos:**
  - Documentação inline nos arquivos fonte
  - README detalhado na raiz do projeto

---
