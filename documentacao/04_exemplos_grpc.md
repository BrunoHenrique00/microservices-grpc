# Exemplos de Chamadas gRPC

Este documento apresenta exemplos de chamadas gRPC utilizando o serviço definido em `protos/servico.proto`. Os exemplos cobrem os principais tipos de chamadas gRPC:

- Unary (requisição-resposta simples)
- Server Streaming (resposta em fluxo)
- Client Streaming (requisição em fluxo)
- Bidirectional Streaming (fluxo bidirecional)

## 1. Unary

O cliente envia uma requisição e recebe uma única resposta.

```python
# Exemplo em Python
```
    response = stub.SuaFuncaoClientStreaming(request_generator())
        for valor in ["a", "b", "c"]:
1. Gere os arquivos a partir do proto:
````markdown
# Exemplos de Chamadas gRPC (práticos)

Este documento mostra exemplos práticos dos quatro tipos de RPC definidos em `protos/servico.proto` e inclui scripts Python prontos para executar.

Serviços definidos no proto (resumo):
- `ServicoA.RealizarTarefaA` — Unary
- `ServicoB.RealizarTarefaB` — Server-streaming
- `ServicoC.RealizarTarefaC` — Client-streaming
- `ServicoD.RealizarTarefaD` — Bidirectional-streaming

Observação: por padrão, no projeto os endpoints gRPC ficam em:
- Módulo A (gRPC): localhost:50051
- Módulo B (gRPC): localhost:50052
Se os teus containers/serviços usarem portas diferentes, ajuste os exemplos.

## Arquivos de exemplo em Python

Criei exemplos prontos em `examples/python/`:

- `client_unary.py` — chama `ServicoA.RealizarTarefaA` (unary)
- `client_server_streaming.py` — chama `ServicoB.RealizarTarefaB` (server-streaming)
- `client_client_streaming.py` — envia múltiplas `RequestC` e recebe `ResponseC`
- `client_bidi_streaming.py` — exemplo simples de bidirectional streaming com threads

### Gerando os stubs Python (onde gerar)

Recomendo gerar os arquivos Python (`servico_pb2.py` e `servico_pb2_grpc.py`) dentro da pasta `examples/python` para que os scripts importem diretamente:

```bash
cd examples/python
python -m grpc_tools.protoc -I../../protos --python_out=. --grpc_python_out=. ../../protos/servico.proto
```

Após gerar os stubs, basta executar cada script, por exemplo:

```bash
python client_unary.py
```

> Se preferir gerar stubs para Node.js, um comando equivalente (usando grpc_tools_node_protoc) pode ser usado e os exemplos Node ficariam em `examples/node/`.

---

## Exemplos (resumo rápido dos scripts)

1) Unary — `client_unary.py`

O script cria uma requisição `RequestA` e chama `RealizarTarefaA` no `ServicoA`:

```python
import grpc
import servico_pb2
import servico_pb2_grpc

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = servico_pb2_grpc.ServicoAStub(channel)
    req = servico_pb2.RequestA(id='req-1', data='hello', operation='uppercase')
    resp = stub.RealizarTarefaA(req)
    print('Response:', resp)

if __name__ == '__main__':
    run()
```

2) Server-streaming — `client_server_streaming.py`

O cliente envia `RequestB` para `ServicoB.RealizarTarefaB` e itera sobre o stream de `ResponseB`:

```python
import grpc
import servico_pb2
import servico_pb2_grpc

def run():
    channel = grpc.insecure_channel('localhost:50052')
    stub = servico_pb2_grpc.ServicoBStub(channel)
    req = servico_pb2.RequestB(id='req-2', data='hello_stream', count=3)
    for resp in stub.RealizarTarefaB(req):
        print('Partial response:', resp)

if __name__ == '__main__':
    run()
```

3) Client-streaming — `client_client_streaming.py`

O cliente gera várias `RequestC` e envia ao método `RealizarTarefaC` então recebe uma `ResponseC` consolidada:

```python
import grpc
import servico_pb2
import servico_pb2_grpc

def request_generator():
    for i, part in enumerate(['p1','p2','p3'], start=1):
        yield servico_pb2.RequestC(id='req-3', data=part, part=i)

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = servico_pb2_grpc.ServicoCStub(channel)
    resp = stub.RealizarTarefaC(request_generator())
    print('Final response:', resp)

if __name__ == '__main__':
    run()
```

4) Bidirectional — `client_bidi_streaming.py`

Exemplo simples que envia mensagens e imprime respostas conforme chegam (usa thread para envio):

```python
import grpc
import servico_pb2
import servico_pb2_grpc
import threading
import time

def request_generator(out_messages):
    for i, m in enumerate(out_messages, start=1):
        yield servico_pb2.RequestD(id=f'req-4', data=m, sequence=i)
        time.sleep(0.2)

def run():
    channel = grpc.insecure_channel('localhost:50052')
    stub = servico_pb2_grpc.ServicoDStub(channel)
    out_messages = ['m1','m2','m3']
    responses = stub.RealizarTarefaD(request_generator(out_messages))
    for resp in responses:
        print('Bidi response:', resp)

if __name__ == '__main__':
    run()
```

---

## Observações finais

- Ajuste endereços/portas conforme o ambiente (docker-compose ou k8s).
- Os scripts assumem que os stubs Python (`servico_pb2.py`, `servico_pb2_grpc.py`) foram gerados no mesmo diretório.
- Se algum serviço não expor `ServicoC`/`ServicoD`, utilize a mesma porta do serviço que os implementa no teu deploy (A/B), ou adicione/ajuste a implementação no código do microserviço.

````
