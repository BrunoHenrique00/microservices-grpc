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
def run_unary_example(stub):
    request = servico_pb2.SuaMensagemRequest(campo="valor")
    response = stub.SuaFuncaoUnary(request)
    print("Resposta:", response)
```

## 2. Server Streaming

O cliente envia uma requisição e recebe um fluxo de respostas do servidor.

```python
# Exemplo em Python
def run_server_streaming_example(stub):
    request = servico_pb2.SuaMensagemRequest(campo="valor")
    for response in stub.SuaFuncaoServerStreaming(request):
        print("Resposta parcial:", response)
```

## 3. Client Streaming

O cliente envia um fluxo de requisições e recebe uma única resposta do servidor.

```python
# Exemplo em Python
def run_client_streaming_example(stub):
    def request_generator():
        for valor in ["a", "b", "c"]:
            yield servico_pb2.SuaMensagemRequest(campo=valor)
    response = stub.SuaFuncaoClientStreaming(request_generator())
    print("Resposta:", response)
```

## 4. Bidirectional Streaming

O cliente e o servidor trocam fluxos de mensagens simultaneamente.

```python
# Exemplo em Python
def run_bidi_streaming_example(stub):
    def request_generator():
        for valor in ["a", "b", "c"]:
            yield servico_pb2.SuaMensagemRequest(campo=valor)
    for response in stub.SuaFuncaoBidiStreaming(request_generator()):
        print("Resposta parcial:", response)
```

---

> **Observação:**
> Substitua `SuaMensagemRequest`, `SuaFuncaoUnary`, etc., pelos nomes reais definidos no seu arquivo `servico.proto`.
> Para rodar os exemplos, gere os arquivos Python a partir do proto e utilize o stub gerado.

## Como executar os exemplos

1. Gere os arquivos a partir do proto:
   ```bash
   python -m grpc_tools.protoc -I../protos --python_out=. --grpc_python_out=. ../protos/servico.proto
   ```
2. Importe o stub e execute as funções de exemplo em um script Python.

Consulte o arquivo `servico.proto` para detalhes dos métodos disponíveis.
