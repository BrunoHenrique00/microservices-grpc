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

## Configuração e Execução

### Opção 1: Usando Docker Compose (Recomendado)

1. **Clone e navegue para o diretório do projeto:**

```bash
cd projeto_distribuido
```

2. **Inicie todos os serviços:**

```bash
docker-compose up --build
```

3. **Aguarde todos os serviços ficarem prontos.** Você verá logs similares a:

```
modulo-a-grpc  | 🚀 Módulo A - Servidor gRPC iniciado!
modulo-b-grpc  | 🚀 Módulo B - Servidor gRPC iniciado!
modulo-p-gateway | 🚀 Módulo P (Gateway) iniciado!
```

### Opção 2: Execução Local (Desenvolvimento)

#### 1. Preparar Módulo P (Gateway)

```bash
cd modulo_P
pip install -r requirements.txt
python generate_protos.py
python app.py
```

#### 2. Preparar Módulo A

```bash
cd modulo_A
npm install
npm start
```

#### 3. Preparar Módulo B

```bash
cd modulo_B
npm install
npm start
```

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

Foi criado um frontend simples para facilitar os testes sem usar o terminal.

### Como Usar o Frontend

1. **Certifique-se de que o backend está rodando:**

```bash
docker-compose up -d
```

2. **Inicie o frontend:**

```bash
cd frontend
npm install
npm start
```

3. **Acesse no navegador:**

```
http://localhost:3000
```

### Funcionalidades do Frontend

- ✅ **Teste Principal**: Testa o fluxo completo (Gateway → Módulo A → Módulo B)
- ✅ **Teste Módulo A**: Testa diretamente o endpoint REST do Módulo A
- ✅ **Teste Módulo B**: Testa diretamente o endpoint REST do Módulo B
- ✅ **Interface Simples**: Formulários intuitivos para todos os testes
- ✅ **Auto-start**: Módulos REST iniciam automaticamente
