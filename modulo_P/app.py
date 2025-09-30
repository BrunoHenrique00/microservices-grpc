"""
Módulo P - Gateway/Proxy em Python com FastAPI
Este módulo atua como um gateway que recebe requisições HTTP
e as converte em chamadas gRPC para os módulos A e B.
"""

import grpc
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import sys
import os

# Adiciona o diretório dos protobuf ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'protos'))

# Importa os stubs gerados a partir do .proto
# Nota: Execute 'python -m grpc_tools.protoc' para gerar os stubs
try:
    import servico_pb2
    import servico_pb2_grpc
except ImportError:
    print("Erro: Execute 'python generate_protos.py' para gerar os stubs gRPC")
    sys.exit(1)

app = FastAPI(title="Módulo P - Gateway", version="1.0.0")

# Modelos Pydantic para validação das requisições HTTP
class ExecutarRequest(BaseModel):
    id: str
    data: str
    operation: str = "default"
    count: int = 3

class ExecutarResponse(BaseModel):
    request_id: str
    resultado_a: Dict[str, Any]
    resultados_b: List[Dict[str, Any]]
    status: str
    message: str

class GRPCClient:
    """Cliente gRPC para comunicação com os módulos A e B"""
    
    def __init__(self):
        # Configuração dos canais gRPC usando variáveis de ambiente
        modulo_a_host = os.getenv('MODULO_A_HOST', 'localhost')
        modulo_a_port = os.getenv('MODULO_A_PORT', '50051')
        modulo_b_host = os.getenv('MODULO_B_HOST', 'localhost') 
        modulo_b_port = os.getenv('MODULO_B_PORT', '50052')
        
        self.channel_a = grpc.insecure_channel(f'{modulo_a_host}:{modulo_a_port}')
        self.channel_b = grpc.insecure_channel(f'{modulo_b_host}:{modulo_b_port}')
        
        # Criação dos stubs
        self.stub_a = servico_pb2_grpc.ServicoAStub(self.channel_a)
        self.stub_b = servico_pb2_grpc.ServicoBStub(self.channel_b)
    
    def close_connections(self):
        """Fecha as conexões gRPC"""
        self.channel_a.close()
        self.channel_b.close()
    
    def chamar_servico_a(self, request_data: ExecutarRequest) -> Dict[str, Any]:
        """
        Chama o serviço A (método unary)
        """
        try:
            # Prepara a requisição para o serviço A
            request_a = servico_pb2.RequestA(
                id=request_data.id,
                data=request_data.data,
                operation=request_data.operation
            )
            
            # Faz a chamada gRPC unary
            response_a = self.stub_a.RealizarTarefaA(request_a, timeout=10)
            
            return {
                "id": response_a.id,
                "result": response_a.result,
                "message": response_a.message,
                "status_code": response_a.status_code
            }
        
        except grpc.RpcError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Erro na comunicação com Módulo A: {e.details()}"
            )
    
    def chamar_servico_b(self, request_data: ExecutarRequest, resultado_a: str) -> List[Dict[str, Any]]:
        """
        Chama o serviço B (método server-streaming)
        """
        try:
            # Prepara a requisição para o serviço B, usando o resultado de A
            request_b = servico_pb2.RequestB(
                id=request_data.id,
                data=f"{request_data.data}_processado_por_A:{resultado_a}",
                count=request_data.count
            )
            
            # Faz a chamada gRPC server-streaming
            responses_b = []
            for response_b in self.stub_b.RealizarTarefaB(request_b, timeout=30):
                responses_b.append({
                    "id": response_b.id,
                    "result": response_b.result,
                    "message": response_b.message,
                    "sequence_number": response_b.sequence_number,
                    "is_final": response_b.is_final
                })
            
            return responses_b
        
        except grpc.RpcError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Erro na comunicação com Módulo B: {e.details()}"
            )

# Instância global do cliente gRPC
grpc_client = GRPCClient()

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização do servidor"""
    print("🚀 Módulo P (Gateway) iniciado!")
    print("📡 Conectando aos módulos A (porta 50051) e B (porta 50052)")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento do servidor"""
    print("🔌 Fechando conexões gRPC...")
    grpc_client.close_connections()

@app.get("/")
async def root():
    """Endpoint de health check"""
    return {
        "service": "Módulo P - Gateway",
        "status": "running",
        "endpoints": ["/api/executar"]
    }

@app.post("/api/executar", response_model=ExecutarResponse)
async def executar_tarefa(request: ExecutarRequest):
    """
    Endpoint principal que orquestra as chamadas para os módulos A e B
    
    Fluxo:
    1. Recebe requisição HTTP do cliente web
    2. Chama o serviço A (unary)
    3. Usa a resposta de A para chamar o serviço B (server-streaming)
    4. Consolida e retorna as respostas
    """
    print(f"📨 Recebida requisição: {request.id}")
    
    try:
        # Passo 1: Chamar o Módulo A
        print(f"🔄 Chamando Módulo A para ID: {request.id}")
        resultado_a = grpc_client.chamar_servico_a(request)
        
        # Passo 2: Chamar o Módulo B usando resultado de A
        print(f"🔄 Chamando Módulo B para ID: {request.id}")
        resultados_b = grpc_client.chamar_servico_b(request, resultado_a["result"])
        
        # Passo 3: Consolidar respostas
        response = ExecutarResponse(
            request_id=request.id,
            resultado_a=resultado_a,
            resultados_b=resultados_b,
            status="success",
            message=f"Tarefa {request.id} executada com sucesso. "
                   f"Módulo A processou, Módulo B retornou {len(resultados_b)} respostas."
        )
        
        print(f"✅ Tarefa {request.id} concluída com sucesso")
        return response
    
    except Exception as e:
        print(f"❌ Erro na execução da tarefa {request.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno na execução da tarefa: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde do serviço"""
    return {
        "status": "healthy",
        "service": "Módulo P",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🌐 Iniciando servidor FastAPI do Módulo P...")
    print("📍 Servidor rodará em: http://localhost:8000")
    print("📋 Documentação da API: http://localhost:8000/docs")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )