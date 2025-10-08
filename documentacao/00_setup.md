# Setup rápido do ambiente (venv, dependências e stubs) — Linux / WSL

Este guia contém apenas as instruções para Linux / WSL (Ubuntu).

## Pré-requisitos
- Python 3.10+ instalado
- python3-venv (WSL/Ubuntu): `sudo apt install -y python3-venv`
- pip
- Docker e Minikube (opcional, para testes em cluster)

## 1) Criar e ativar virtualenv (Linux / WSL)
```bash
# a partir da raiz do repositório
python3 -m venv .venv
source .venv/bin/activate
```

## 2) Atualizar pip e instalar dependências básicas (gRPC / protobuf)
```bash
# com o .venv ativo
python3 -m pip install --upgrade pip
python3 -m pip install grpcio grpcio-tools protobuf
# (opcional) instalar requirements do modulo_P caso exista
# python3 -m pip install -r modulo_P/requirements.txt
```

## 3) Gerar stubs Python a partir do .proto
```bash
# gerará servico_pb2.py e servico_pb2_grpc.py em examples/python
python3 -m grpc_tools.protoc -Iprotos --python_out=examples/python --grpc_python_out=examples/python protos/servico.proto
```

## 4) Executar exemplos locais (mocks inline)
```bash
python3 examples/python/test_run_unary_local.py
python3 examples/python/test_run_server_streaming_local.py
python3 examples/python/test_run_client_streaming_local.py
python3 examples/python/test_run_bidi_local.py
```

## 5) Testar contra serviços no Minikube (port-forward)
- Abra port-forward em terminais separados e deixe-os rodando:
```bash
# módulo A (gRPC)
minikube kubectl -- port-forward svc/modulo-a-service 50051:50051 -n projeto-distribuido

# módulo B (gRPC)
minikube kubectl -- port-forward svc/modulo-b-service 50052:50052 -n projeto-distribuido

# Gateway (HTTP)
minikube kubectl -- port-forward svc/modulo-p-service 8000:8000 -n projeto-distribuido
```

- Em outro terminal (com .venv ativo) rode os clientes apontando para localhost:50051 / 50052:
```bash
python3 examples/python/client_unary.py
python3 examples/python/client_server_streaming.py
```

## 6) Problemas comuns e soluções rápidas
- `ModuleNotFoundError: grpc`
  - Verifique se o .venv está ativado e se instalou grpcio no mesmo Python.
- Erro ao bind na porta (ex: 127.0.0.1:50051)
  - Verifique processo ocupando a porta: `ss -ltnp | grep 50051` ou `sudo lsof -iTCP:50051 -sTCP:LISTEN`
  - Pare o processo ou mapeie para outra porta local (ex.: `50551:50051`).
- Minikube start com driver docker em root
  - Não execute minikube como root. Saia de root e garanta que seu usuário esteja no grupo docker:
    ```bash
    sudo usermod -aG docker $USER
    newgrp docker
    ```
  - Se realmente precisar, use `minikube start --driver=docker --force` (não recomendado).
- Stubs não gerados dentro do container do Gateway
  - Gere os stubs localmente antes do build ou ajuste o Dockerfile para gerar durante a imagem (ver modulo_P/generate_protos.py).

## 7) Executando o deploy (opcional)
- Use o script automatizado:
```bash
chmod +x kubernetes_start.sh
./kubernetes_start.sh
```
- Se der erro relacionado a execução como root, siga a recomendação acima (não rodar minikube como root).

## 8) Testes e debug
```bash
minikube kubectl -- get pods -n projeto-distribuido
minikube kubectl -- get svc -n projeto-distribuido
minikube kubectl -- logs <POD_NAME> -n projeto-distribuido --tail=200
```

## Notas finais

- Este arquivo é um guia mínimo para Linux/WSL
