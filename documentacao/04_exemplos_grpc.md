# Exemplos de Chamadas gRPC

Resumo

Este documento reúne exemplos práticos dos quatro tipos de RPC definidos em `protos/servico.proto` e mostra como gerar os stubs e executar os clientes de exemplo em Python.

Serviços (resumo)

- `ServicoA.RealizarTarefaA` — Unary
- `ServicoB.RealizarTarefaB` — Server-streaming
- `ServicoC.RealizarTarefaC` — Client-streaming
- `ServicoD.RealizarTarefaD` — Bidirectional-streaming

Pré-requisitos

- Python 3.11+ (ou o Python configurado no projeto)
- pacote `grpcio` e `grpcio-tools` instalados (veja `requirements.txt` do `modulo_P`)
- As portas padrões usadas nos exemplos:
  - Módulo A (gRPC): `localhost:50051`
  - Módulo B (gRPC): `localhost:50052`

Gerar os stubs Python

Gere os arquivos `servico_pb2.py` e `servico_pb2_grpc.py` dentro de `examples/python`:

```bash
cd examples/python
python -m grpc_tools.protoc -I../../protos --python_out=. --grpc_python_out=. ../../protos/servico.proto
```

Executando os exemplos (modo rápido com mocks inline)

Os testes criados em `examples/python/` iniciam servidores mock inline (não dependem do Docker). São úteis para validar funcionalidade localmente.

No Windows (PowerShell) execute:

```powershell
C:/Python312/python.exe .\examples\python\test_run_unary_local.py
C:/Python312/python.exe .\examples\python\test_run_server_streaming_local.py
C:/Python312/python.exe .\examples\python\test_run_client_streaming_local.py
C:/Python312/python.exe .\examples\python\test_run_bidi_local.py
```

Ou em Linux/macOS (bash):

```bash
python3 examples/python/test_run_unary_local.py
python3 examples/python/test_run_server_streaming_local.py
python3 examples/python/test_run_client_streaming_local.py
python3 examples/python/test_run_bidi_local.py
```

Clientes individuais

- `examples/python/client_unary.py` — Chama `ServicoA.RealizarTarefaA`.
- `examples/python/client_server_streaming.py` — Chama `ServicoB.RealizarTarefaB` e itera sobre o stream.
- `examples/python/client_client_streaming.py` — Envia múltiplas `RequestC` e recebe `ResponseC` agregada.
- `examples/python/client_bidi_streaming.py` — Comunicação bidirecional exemplo.

Trecho de exemplo (unary)

```python
import grpc
import servico_pb2
import servico_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = servico_pb2_grpc.ServicoAStub(channel)
req = servico_pb2.RequestA(id='req-1', data='hello', operation='uppercase')
resp = stub.RealizarTarefaA(req)
print('Response:', resp)
```

Boas práticas e observações

- Sempre regenere os stubs se modificar `protos/servico.proto`.
- Se for executar com Docker Compose, use as portas mapeadas no `docker-compose.yml`.
- Em ambiente Windows atente para finais de linha (CRLF) e para o caminho do executável Python.
- Se preferir exemplos em Node.js, podemos adicionar clientes equivalentes em `examples/node/`.

Troubleshooting rápido

- Erro de conexão (Connection refused): verifique se o serviço alvo está em execução e a porta correta.
- Erro de versão do grpc ao importar stubs: alinhe a versão de `grpcio`/`grpcio-tools` usada para gerar os stubs.

Referências

- `protos/servico.proto`
- `examples/python/README.md` (instruções específicas dos exemplos)
