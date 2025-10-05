"""
Script para teste de performance dos endpoints do Módulo P
Compara tempo de resposta entre gRPC e REST/JSON
"""
import requests
import time
import json

API_URL = "http://localhost:8000/api/executar"
N_REQUESTS = 10
PAYLOAD = {
    "id": "test",
    "data": "exemplo",
    "operation": "upper",
    "count": 3
}

def testar_endpoint():
    tempos = []
    for i in range(N_REQUESTS):
        inicio = time.time()
        resp = requests.post(API_URL, json=PAYLOAD)
        fim = time.time()
        tempos.append(fim - inicio)
        if resp.status_code != 200:
            print(f"Erro na requisição {i}: {resp.status_code}")
    print(f"Tempo médio: {sum(tempos)/len(tempos):.4f} segundos")
    print(f"Menor tempo: {min(tempos):.4f} s | Maior tempo: {max(tempos):.4f} s")

if __name__ == "__main__":
    print(f"Testando {N_REQUESTS} requisições para {API_URL}")
    testar_endpoint()
    print("Altere o modo de comunicação do Módulo P (gRPC/REST) e repita o teste.")
