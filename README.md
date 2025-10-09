# Projeto Distribuído com gRPC

Este projeto implementa uma aplicação distribuída baseada em gRPC com três módulos principais: **P** (Gateway), **A** e **B** (Microserviços).

## Arquitetura

```
WEB Client (HTTP) -> Módulo P (Gateway/FastAPI) -> Módulo A (gRPC/Node.js)
                                                 -> Módulo B (gRPC/Node.js)
```

- **Módulo P**: Gateway/Proxy em Python com FastAPI que recebe requisições HTTP e as converte em chamadas gRPC
- **Módulo A**: Microserviço gRPC em Node.js com método unary
- **Módulo B**: Microserviço gRPC em Node.js com método server-streaming

## Estrutura do Projeto

```
projeto_distribuido/
├── protos/
│   └── servico.proto           # Definições gRPC (mensagens e serviços)
├── modulo_P/                   # Gateway FastAPI (Python)
│   ├── app.py                  # Servidor FastAPI principal
│   ├── generate_protos.py      # Script para gerar stubs Python
│   ├── requirements.txt        # Dependências Python
│   └── Dockerfile              # Container do gateway
├── modulo_A/                   # Microserviço A (Node.js)
│   ├── server.js               # Servidor gRPC com método unary
│   ├── package.json            # Dependências Node.js
│   └── Dockerfile              # Container do módulo A
├── modulo_B/                   # Microserviço B (Node.js)
│   ├── server.js               # Servidor gRPC com streaming
│   ├── package.json            # Dependências Node.js
│   └── Dockerfile              # Container do módulo B
├── docker-compose.yml          # Orquestração dos serviços
└── README.md                   # Este arquivo
```

## Requisitos

- **Docker** e **Docker Compose**
- **Python 3.11+** (para desenvolvimento local)
- **Node.js 18+** (para desenvolvimento local)

## Como rodar o sistema (tudo via Docker Compose)

1. Certifique-se de ter Docker e Docker Compose instalados.
2. No diretório raiz do projeto, execute:

```bash
docker compose up --build -d
```

3. Acesse o frontend em [http://localhost:3000](http://localhost:3000)
4. O gateway (Módulo P) estará disponível em [http://localhost:8000](http://localhost:8000)

5. Para ver logs em tempo real:

```bash
docker compose logs -f
```

6. Para parar tudo:

```bash
docker compose down
```

---

## Como alternar entre gRPC e REST/JSON

Para alternar entre gRPC e REST/JSON, edite o serviço `modulo-p` no `docker-compose.yml`:

```yaml
environment:
  - MODOP_COMUNICACAO=rest # ou 'grpc' (padrão)
```

Depois, reinicie os containers:

```bash
docker compose up --build -d
```

---

## Como Usar

### 1. Verificar Status dos Serviços

- **Gateway (Módulo P)**: http://localhost:8000
- **Documentação da API**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 2. Fazer Requisições

**Endpoint Principal**: `POST http://localhost:8000/api/executar`

**Payload de exemplo**:

```json
{
  "id": "tarefa-001",
  "data": "dados_de_teste",
  "operation": "uppercase",
  "count": 3
}
```

**Exemplo com curl**:

```bash
curl -X POST "http://localhost:8000/api/executar" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "tarefa-001",
       "data": "hello_world",
       "operation": "uppercase",
       "count": 3
     }'
```

### 3. Resposta Esperada

```json
{
  "request_id": "tarefa-001",
  "resultado_a": {
    "id": "tarefa-001",
    "result": "HELLO_WORLD_PROCESSED_AT_2025-09-29T10:30:00.000Z",
    "message": "Tarefa A executada com sucesso para ID tarefa-001",
    "status_code": 200
  },
  "resultados_b": [
    {
      "id": "tarefa-001",
      "result": "hello_world_processado_por_A:HELLO_WORLD_PROCESSED_AT_2025-09-29T10:30:00.000Z_chunk_1_analyzed_progress_33.3%_at_2025-09-29T10:30:01.000Z",
      "message": "Resposta 1 de 3 do ServicoB",
      "sequence_number": 1,
      "is_final": false
    },
    {
      "id": "tarefa-001",
      "result": "hello_world_processado_por_A:HELLO_WORLD_PROCESSED_AT_2025-09-29T10:30:00.000Z_chunk_2_transformed_progress_66.7%_at_2025-09-29T10:30:02.000Z",
      "message": "Resposta 2 de 3 do ServicoB",
      "sequence_number": 2,
      "is_final": false
    },
    {
      "id": "tarefa-001",
      "result": "hello_world_processado_por_A:HELLO_WORLD_PROCESSED_AT_2025-09-29T10:30:00.000Z_chunk_3_enriched_progress_100.0%_at_2025-09-29T10:30:03.000Z",
      "message": "Resposta 3 de 3 do ServicoB",
      "sequence_number": 3,
      "is_final": true
    }
  ],
  "status": "success",
  "message": "Tarefa tarefa-001 executada com sucesso. Módulo A processou, Módulo B retornou 3 respostas."
}
```

## Testando os Endpoints REST dos Módulos A e B

Você pode testar os microsserviços REST/JSON (modulo_A e modulo_B) diretamente usando `curl` ou Postman.

### Módulo A (REST)

Inicie o servidor REST do módulo A:

```bash
cd modulo_A
npm install express
node server_rest.js
```

Teste o endpoint:

```bash
curl -X POST http://localhost:5001/realizar-tarefa-a \
  -H "Content-Type: application/json" \
  -d '{"id":1,"data":"exemplo","operation":"upper"}'
```

Resposta esperada:

```json
{ "id": 1, "resultado": "EXEMPLO", "status": "ok" }
```

### Módulo B (REST)

Inicie o servidor REST do módulo B:

```bash
cd modulo_B
npm install express
node server_rest.js
```

Teste o endpoint:

```bash
curl -X POST http://localhost:5002/realizar-tarefa-b \
  -H "Content-Type: application/json" \
  -d '{"id":2,"data":"exemplo","count":3}'
```

Resposta esperada:

```json
{
  "id": 2,
  "respostas": [
    { "id": 2, "resultado": "exemplo-resp1", "ordem": 1, "status": "ok" },
    { "id": 2, "resultado": "exemplo-resp2", "ordem": 2, "status": "ok" },
    { "id": 2, "resultado": "exemplo-resp3", "ordem": 3, "status": "ok" }
  ],
  "total": 3
}
```

## Fluxo de Execução

1. **Cliente Web** faz requisição HTTP POST para `/api/executar`
2. **Módulo P** recebe a requisição e:
   - Chama o **Módulo A** via gRPC (método unary)
   - Usa a resposta do **Módulo A** para chamar o **Módulo B** via gRPC (método server-streaming)
   - Consolida as respostas e retorna ao cliente como JSON

## Operações Disponíveis (Módulo A)

- `uppercase`: Converte para maiúsculas
- `lowercase`: Converte para minúsculas
- `reverse`: Inverte a string
- `length`: Retorna o comprimento
- `default`: Processamento padrão

## Teste de Performance: Comparativo gRPC vs REST/JSON

O script `documentacao/teste_performance.py` permite comparar o tempo de resposta do endpoint principal do Módulo P, tanto usando gRPC quanto REST/JSON.

### Para que serve?

Esse script faz múltiplas requisições POST para o endpoint `/api/executar` do Módulo P e mede o tempo de resposta médio, mínimo e máximo. Você pode alternar o modo de comunicação do Módulo P (gRPC ou REST) e comparar os resultados para cada abordagem.

### Como usar

1. **Crie e ative um ambiente virtual Python:**

```bash
python3 -m venv venv
source venv/bin/activate
```

2. **Instale a dependência necessária:**

```bash
pip install requests
```

3. **Execute o script de teste:**

```bash
python documentacao/teste_performance.py
```

4. **Altere o modo de comunicação do Módulo P:**

- Para testar gRPC, mantenha `MODOP_COMUNICACAO=grpc` (padrão)
- Para testar REST, defina `MODOP_COMUNICACAO=rest` antes de iniciar o Módulo P:
  ```bash
  export MODOP_COMUNICACAO=rest
  python app.py
  ```

5. **Compare os resultados exibidos pelo script** (tempo médio, menor e maior tempo).

### Exemplo de saída

```
Testando 10 requisições para http://localhost:8000/api/executar
Tempo médio: 3.0348 segundos
Menor tempo: 3.0304 s | Maior tempo: 3.0500 s
Altere o modo de comunicação do Módulo P (gRPC/REST) e repita o teste.
```

## Monitoramento

### Logs dos Serviços

```bash
# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f modulo-a
docker-compose logs -f modulo-b
docker-compose logs -f modulo-p
```

### Health Checks

Os serviços incluem health checks configurados no Docker Compose:

```bash
# Verificar status dos containers
docker-compose ps
```

## Desenvolvimento

### Modificar o Arquivo .proto

Quando modificar `protos/servico.proto`:

1. **Para o Módulo P**:

```bash
cd modulo_P
python generate_protos.py
```

2. **Para os Módulos A e B**:
   Os stubs são carregados dinamicamente, não é necessário regenerar.

### Debugging

Para debugging local, você pode executar cada módulo separadamente:

1. Primeiro inicie os módulos A e B
2. Depois inicie o módulo P
3. Use as portas padrão: A (50051), B (50052), P (8000)

## Portas Utilizadas

- **Módulo P (Gateway)**: 8000 (HTTP)
- **Módulo A**: 50051 (gRPC)
- **Módulo B**: 50052 (gRPC)

## Parar os Serviços

```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes
docker-compose down -v

# Forçar reconstrução na próxima execução
docker-compose down --rmi all
```

## 🌐 Frontend para Testes

O frontend já está incluso no Docker Compose. Basta rodar:

```bash
docker compose up --build -d
```

E acessar no navegador:

```
http://localhost:3000
```

Funcionalidades do Frontend:

- ✅ **Teste Principal**: Testa o fluxo completo (Gateway → Módulo A → Módulo B)
- ✅ **Teste Módulo A**: Testa diretamente o endpoint REST do Módulo A
- ✅ **Teste Módulo B**: Testa diretamente o endpoint REST do Módulo B
- ✅ **Interface Simples**: Formulários intuitivos para todos os testes
- ✅ **Auto-start**: Módulos REST iniciam automaticamente

## Comparação de Desempenho gRPC x REST no Frontend

O frontend web deste projeto possui um painel de **Comparação gRPC x REST** que permite comparar, de forma prática e visual, o tempo de resposta entre os dois tipos de comunicação.

### Como funciona o teste de comparação

- O frontend envia **5 requisições** para o gateway (gRPC) e para o endpoint REST do Módulo A.
- Para gRPC, a requisição segue o fluxo: **Frontend → Gateway (FastAPI) → gRPC → Módulo A (Node.js)**.
- Para REST, a requisição vai **direto do Frontend para o endpoint REST do Módulo A (Node.js)**.
- O tempo de resposta de cada requisição é medido individualmente e a média dos tempos é calculada para cada abordagem.
- O resultado mostra:
  - A média dos tempos de resposta para gRPC e REST
  - Os tempos individuais de cada requisição
  - A diferença média entre gRPC e REST
  - Indicação visual de qual abordagem foi mais rápida

### O que está sendo comparado?

- **gRPC (via gateway):** Mede o tempo total do caminho Frontend → FastAPI (gateway) → gRPC → Node.js → resposta. Inclui o overhead do gateway e do protocolo gRPC.
- **REST (direto):** Mede o tempo do caminho Frontend → Node.js (REST) → resposta, sem intermediários.

## Deploy com Kubernetes (Minikube)

Esta seção detalha como implantar a aplicação em um cluster Kubernetes local utilizando o Minikube, simulando um ambiente de produção Cloud Native.

### Arquivos de Configuração

O deploy no Kubernetes é definido de forma declarativa através dos arquivos de manifesto (`.yaml`) localizados na pasta `kubernetes/`.

- `01-namespace.yaml`: Cria um espaço de trabalho isolado chamado `projeto-distribuido` para organizar todos os recursos da nossa aplicação.
- `modulo-a-deployment.yaml`: Define o estado desejado para o Módulo A, especificando a imagem Docker a ser usada e o número de réplicas.
- `modulo-a-service.yaml`: Expõe o Módulo A internamente no cluster (`ClusterIP`), permitindo que o Gateway P o encontre através do nome `modulo-a-service`.
- `modulo-b-deployment.yaml`: Define o estado desejado para o Módulo B.
- `modulo-b-service.yaml`: Expõe o Módulo B internamente no cluster (`ClusterIP`) com o nome `modulo-b-service`.
- `modulo-p-deployment.yaml`: Define o estado desejado para o Módulo P (Gateway).
- `modulo-p-service.yaml`: Expõe o Gateway para acesso externo através de uma porta no nó do cluster (`NodePort`), tornando a aplicação acessível para o usuário.

### Instruções para o Deploy do Backend

O script `kubernetes_start.sh` automatiza todo o processo de deploy do backend.

1.  **Dê permissão de execução ao script:**

    ```bash
    chmod +x kubernetes_start.sh
    ```

2.  **Execute o script de deploy:**
    ```bash
    ./kubernetes_start.sh
    ```
    O script irá realizar as seguintes etapas:
    - Verificar se Docker e Minikube estão instalados.
    - Iniciar o cluster Minikube.
    - Conectar o ambiente Docker ao daemon do Minikube.
    - Construir as imagens Docker dos três módulos.
    - Aplicar todos os manifestos `.yaml` na ordem correta.
    - Aguardar até que todos os Pods estejam no estado `Running`.

### Acessando a Aplicação (Frontend + Backend)

Após o script `kubernetes_start.sh` finalizar, seu backend estará rodando no Kubernetes. Para interagir com a aplicação através da interface web, siga os passos:

1.  **Obtenha a URL do Backend (Gateway):**
    Abra um **novo terminal** e execute o comando abaixo para descobrir o endereço do seu gateway.

    ```bash
    minikube service modulo-p-service -n projeto-distribuido --url
    ```

    Copie a URL retornada (algo como `http://192.168.49.2:30385`).

2.  **Inicie o Servidor do Frontend:**
    Ainda no mesmo terminal, navegue até a pasta `frontend` e inicie o servidor, passando a URL do backend como uma variável de ambiente. Substitua `<URL_DO_MINIKUBE>` pela URL que você copiou.

    **No Linux/macOS:**

    ```bash
    export GATEWAY_URL="<URL_DO_MINIKUBE>"
    cd frontend
    npm install  # Execute apenas na primeira vez
    npm start
    ```

    **No Windows (PowerShell):**

    ```powershell
    $env:GATEWAY_URL="<URL_DO_MINIKUBE>"
    cd frontend
    npm install  # Execute apenas na primeira vez
    npm start
    ```

3.  **Acesse a Interface Web:**
    Abra seu navegador e acesse a URL do frontend, que estará rodando localmente:
    ```
    http://localhost:3000
    ```
    A interface agora estará conectada ao seu backend no Kubernetes e todos os testes funcionarão.

### Gerenciamento do Ambiente

- **Para pausar o cluster** e liberar os recursos (CPU/RAM) do seu computador, execute:
  ```bash
  minikube stop
  ```
- **Para retomar o trabalho**, simplesmente reinicie o cluster (é mais rápido que a primeira vez):
  ```bash
  minikube start
  ```
- **Para apagar completamente o cluster** e todos os recursos, execute:
  ```bash
  minikube delete
  ```

## Entrega

- O relatório e vídeo de apresentação está disponível em: [`relatorio.md`](./relatorio.md)
