"""
Módulo P - Gateway/Proxy em Python com FastAPI
Este módulo atua como um gateway que recebe requisições HTTP/WebSocket
e as converte em chamadas gRPC para os módulos A e B.
Agora inclui suporte para chat em tempo real via WebSocket.
"""

import grpc
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Set
import sys
import os
import requests
import json
import uuid
import base64
from datetime import datetime
import logging
from prometheus_fastapi_instrumentator import Instrumentator

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

app = FastAPI(title="Módulo P - Chat Gateway", version="2.0.0")

Instrumentator().instrument(app).expose(app)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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

# Modelos para Chat
class ChatLoginRequest(BaseModel):
    username: str
    room_id: str = "global"

class ChatMessageRequest(BaseModel):
    username: str
    content: str
    room_id: str = "global"
    message_type: str = "MESSAGE"

# Gerenciador de conexões WebSocket
class ConnectionManager:
    def __init__(self):
        # {room_id: {user_id: {"websocket": ws, "username": str}}}
        self.active_connections: Dict[str, Dict[str, Dict]] = {}
        # Armazenamento em memória das mensagens {room_id: [messages]}
        self.message_history: Dict[str, List[Dict]] = {}
        # Usuários online {room_id: {user_id: user_info}}
        self.online_users: Dict[str, Dict[str, Dict]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, username: str, room_id: str = "global"):
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
            self.message_history[room_id] = []
            self.online_users[room_id] = {}
        
        self.active_connections[room_id][user_id] = {
            "websocket": websocket,
            "username": username
        }
        
        self.online_users[room_id][user_id] = {
            "username": username,
            "status": "ONLINE",
            "joined_at": datetime.now().timestamp()
        }
        
        logger.info(f"User {username} ({user_id}) connected to room {room_id}")
        
        # Notificar outros usuários sobre a entrada
        await self.broadcast_to_room(room_id, {
            "type": "USER_JOIN",
            "username": username,
            "user_id": user_id,
            "timestamp": datetime.now().timestamp(),
            "message": f"{username} entrou no chat"
        }, exclude_user=user_id)
        
        # Enviar lista de usuários online para o novo usuário
        await self.send_online_users(websocket, room_id)
        
        # Enviar histórico de mensagens para o novo usuário
        await self.send_message_history(websocket, room_id)
    
    def disconnect(self, user_id: str, room_id: str = "global"):
        if room_id in self.active_connections and user_id in self.active_connections[room_id]:
            username = self.active_connections[room_id][user_id]["username"]
            del self.active_connections[room_id][user_id]
            
            if user_id in self.online_users.get(room_id, {}):
                del self.online_users[room_id][user_id]
            
            logger.info(f"User {username} ({user_id}) disconnected from room {room_id}")
            return username
        return None
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast_to_room(self, room_id: str, message: dict, exclude_user: str = None):
        if room_id not in self.active_connections:
            return
        logger.info(f"Broadcasting message to room {room_id}: {message}")
        # Só processa mensagens do tipo MESSAGE
        processed_message = message.copy()
        if message.get("type") == "MESSAGE":
            from app import service_client, ExecutarRequest
            try:
                req = ExecutarRequest(
                    id=message.get("id", ""),
                    data=message.get("content", ""),
                    operation="process_message"
                )
                result = service_client.chamar_servico_a(req)
                processed_message["content"] = result.get("result", message.get("content", ""))
                processed_message["processed_by_module_a"] = True
            except Exception as e:
                logger.error(f"Erro ao processar mensagem no Módulo A: {e}")
                processed_message["processed_by_module_a"] = False

        disconnected_users = []
        for user_id, connection_info in self.active_connections[room_id].items():
            if exclude_user and user_id == exclude_user:
                continue
            try:
                await connection_info["websocket"].send_text(json.dumps(processed_message))
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected_users.append(user_id)

        # Remove conexões mortas
        for user_id in disconnected_users:
            self.disconnect(user_id, room_id)
    
    async def send_online_users(self, websocket: WebSocket, room_id: str):
        if room_id in self.online_users:
            users_list = [
                {
                    "user_id": user_id,
                    "username": user_info["username"],
                    "status": user_info["status"]
                }
                for user_id, user_info in self.online_users[room_id].items()
            ]
            
            await self.send_personal_message({
                "type": "ONLINE_USERS",
                "users": users_list,
                "total_count": len(users_list)
            }, websocket)
    
    async def send_message_history(self, websocket: WebSocket, room_id: str, limit: int = 50):
        if room_id in self.message_history:
            recent_messages = self.message_history[room_id][-limit:]
            for message in recent_messages:
                await self.send_personal_message(message, websocket)
    
    def store_message(self, room_id: str, message: dict):
        if room_id not in self.message_history:
            self.message_history[room_id] = []
        
        self.message_history[room_id].append(message)
        
        # Manter apenas as últimas 1000 mensagens em memória
        if len(self.message_history[room_id]) > 1000:
            self.message_history[room_id] = self.message_history[room_id][-1000:]

# Instância global do gerenciador
manager = ConnectionManager()

class ServiceClient:
    """Cliente para comunicação com os módulos A e B via gRPC ou REST"""
    def __init__(self, modo='grpc'):
        self.modo = modo
        # Configuração dos hosts/ports
        self.modulo_a_host = os.getenv('MODULO_A_HOST', 'localhost')
        self.modulo_a_port_grpc = os.getenv('MODULO_A_PORT', '50051')
        self.modulo_a_port_rest = os.getenv('MODULO_A_PORT_REST', '5001')
        self.modulo_b_host = os.getenv('MODULO_B_HOST', 'localhost')
        self.modulo_b_port_grpc = os.getenv('MODULO_B_PORT', '50052')
        self.modulo_b_port_rest = os.getenv('MODULO_B_PORT_REST', '5002')

        if self.modo == 'grpc':
            self.channel_a = grpc.insecure_channel(f'{self.modulo_a_host}:{self.modulo_a_port_grpc}')
            self.channel_b = grpc.insecure_channel(f'{self.modulo_b_host}:{self.modulo_b_port_grpc}')
            self.stub_a = servico_pb2_grpc.ServicoAStub(self.channel_a)
            self.stub_b = servico_pb2_grpc.ServicoBStub(self.channel_b)

    def close_connections(self):
        if self.modo == 'grpc':
            self.channel_a.close()
            self.channel_b.close()

    def chamar_servico_a(self, request_data: ExecutarRequest) -> Dict[str, Any]:
        if self.modo == 'grpc':
            try:
                request_a = servico_pb2.RequestA(
                    id=request_data.id,
                    data=request_data.data,
                    operation=request_data.operation
                )
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
                    detail=f"Erro na comunicação com Módulo A (gRPC): {e.details()}"
                )
        else:
            # REST/JSON
            try:
                url = f"http://{self.modulo_a_host}:{self.modulo_a_port_rest}/realizar-tarefa-a"
                payload = {
                    "id": request_data.id,
                    "data": request_data.data,
                    "operation": request_data.operation
                }
                resp = requests.post(url, json=payload, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Erro na comunicação com Módulo A (REST): {str(e)}"
                )

    def chamar_servico_b(self, request_data: ExecutarRequest, resultado_a: str) -> List[Dict[str, Any]]:
        if self.modo == 'grpc':
            try:
                request_b = servico_pb2.RequestB(
                    id=request_data.id,
                    data=f"{request_data.data}_processado_por_A:{resultado_a}",
                    count=request_data.count
                )
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
                    detail=f"Erro na comunicação com Módulo B (gRPC): {e.details()}"
                )
        else:
            # REST/JSON
            try:
                url = f"http://{self.modulo_b_host}:{self.modulo_b_port_rest}/realizar-tarefa-b"
                payload = {
                    "id": request_data.id,
                    "data": f"{request_data.data}_processado_por_A:{resultado_a}",
                    "count": request_data.count
                }
                resp = requests.post(url, json=payload, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                return data.get("respostas", [])
            except Exception as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Erro na comunicação com Módulo B (REST): {str(e)}"
                )


class GrpcChatClient:
    """Cliente gRPC especializado para operações de chat"""
    def __init__(self):
        self.modulo_a_host = os.getenv('MODULO_A_HOST', 'localhost')
        self.modulo_a_port = os.getenv('MODULO_A_PORT', '50051')
        self.modulo_b_host = os.getenv('MODULO_B_HOST', 'localhost')
        self.modulo_b_port = os.getenv('MODULO_B_PORT', '50052')
        # Armazenar uploads de arquivo em progresso
        self.file_uploads = {}  # {file_id: {"chunks": [], "metadata": {}, "status": "in_progress"}}
    
    def process_message(self, username: str, content: str, room_id: str, user_id: str) -> Dict[str, Any]:
        """
        Processa mensagem via Module A (ChatService)
        Integração: Envia a mensagem para Module A processar antes de repassar para outros usuários
        """
        try:
            channel = grpc.insecure_channel(f'{self.modulo_a_host}:{self.modulo_a_port}')
            stub = servico_pb2_grpc.ServicoAStub(channel)
            
            # Usar RealizarTarefaA para processar a mensagem
            request = servico_pb2.RequestA(
                id=str(uuid.uuid4()),
                data=content,
                operation="process_message"  # Operação especial para processamento de chat
            )
            
            response = stub.RealizarTarefaA(request, timeout=10)
            channel.close()
            
            logger.info(f"✅ Mensagem processada por Module A: {response.result[:50]}...")
            
            return {
                "success": True,
                "processed_content": response.result,
                "original_content": content,
                "status": "processed_by_module_a"
            }
        except grpc.RpcError as e:
            logger.error(f"❌ Erro ao processar mensagem no Module A: {e.details()}")
            # Se Module A falhar, usar conteúdo original
            return {
                "success": False,
                "processed_content": content,
                "original_content": content,
                "status": "fallback_to_original",
                "error": str(e.details())
            }
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com Module A: {str(e)}")
            return {
                "success": False,
                "processed_content": content,
                "original_content": content,
                "status": "fallback_to_original",
                "error": str(e)
            }
    
    def get_online_users(self, room_id: str) -> List[Dict[str, Any]]:
        """
        Obtém lista de usuários online via Module A (UserService)
        """
        try:
            channel = grpc.insecure_channel(f'{self.modulo_a_host}:{self.modulo_a_port}')
            stub = servico_pb2_grpc.UserServiceStub(channel)
            
            request = servico_pb2.OnlineUsersRequest(room_id=room_id)
            response = stub.GetOnlineUsers(request, timeout=10)
            channel.close()
            
            users = []
            for user_info in response.users:
                users.append({
                    "user_id": user_info.user_id,
                    "username": user_info.username,
                    "status": user_info.status,
                    "last_seen": user_info.last_seen
                })
            
            return users
        except Exception as e:
            logger.error(f"Erro ao obter usuários online: {str(e)}")
            return []
    
    def start_file_upload(self, file_id: str, filename: str, mime_type: str, file_size: int, user_id: str, username: str, room_id: str):
        """
        Inicia uma sessão de upload de arquivo
        """
        self.file_uploads[file_id] = {
            "chunks": [],
            "metadata": {
                "file_id": file_id,
                "filename": filename,
                "mime_type": mime_type,
                "file_size": file_size,
                "user_id": user_id,
                "username": username,
                "room_id": room_id,
                "total_chunks": 0,
                "received_chunks": 0
            },
            "status": "in_progress"
        }
        logger.info(f"📎 Iniciando upload: {filename} (ID: {file_id})")
    
    def add_file_chunk(self, file_id: str, chunk_data: bytes, chunk_index: int, total_chunks: int) -> bool:
        """
        Adiciona um chunk ao upload em progresso
        """
        if file_id not in self.file_uploads:
            logger.warning(f"Upload {file_id} não encontrado")
            return False
        
        upload = self.file_uploads[file_id]
        upload["chunks"].append({
            "index": chunk_index,
            "data": chunk_data
        })
        upload["metadata"]["received_chunks"] = chunk_index + 1
        upload["metadata"]["total_chunks"] = total_chunks
        
        logger.info(f"📥 Chunk {chunk_index + 1}/{total_chunks} recebido para {upload['metadata']['filename']}")
        return True
    
    def finalize_file_upload(self, file_id: str) -> Dict[str, Any]:
        """
        Finaliza um upload e envia para Module B via gRPC
        """
        if file_id not in self.file_uploads:
            return {"success": False, "error": "Upload não encontrado"}
        
        upload = self.file_uploads[file_id]
        metadata = upload["metadata"]
        
        try:
            # Combinar chunks em ordem
            sorted_chunks = sorted(upload["chunks"], key=lambda x: x["index"])
            file_data = b"".join([chunk["data"] for chunk in sorted_chunks])
            
            logger.info(f"🔄 Enviando arquivo para Module B: {metadata['filename']}")
            
            # Conectar ao Module B e fazer upload via gRPC
            channel = grpc.insecure_channel(f'{self.modulo_b_host}:{self.modulo_b_port}')
            stub = servico_pb2_grpc.FileServiceStub(channel)
            
            # Gerar chunks para gRPC
            def upload_generator():
                chunk_size = 1024 * 1024  # 1MB
                total_grpc_chunks = (len(file_data) + chunk_size - 1) // chunk_size
                
                for i in range(total_grpc_chunks):
                    start = i * chunk_size
                    end = min(start + chunk_size, len(file_data))
                    chunk = file_data[start:end]
                    
                    yield servico_pb2.FileChunk(
                        file_id=metadata['file_id'],
                        filename=metadata['filename'],
                        mime_type=metadata['mime_type'],
                        chunk_data=chunk,
                        chunk_index=i,
                        total_chunks=total_grpc_chunks,
                        file_size=len(file_data),
                        user_id=metadata['user_id'],
                        username=metadata['username'],
                        room_id=metadata['room_id']
                    )
            
            # Enviar para Module B
            response = stub.UploadFile(upload_generator(), timeout=120)
            channel.close()
            
            upload["status"] = "completed"
            
            logger.info(f"✅ Arquivo enviado para Module B: {metadata['filename']}")
            
            # Preparar resposta para broadcast
            result = {
                "success": True,
                "file_id": metadata['file_id'],
                "filename": metadata['filename'],
                "file_size": len(file_data),
                "user_id": metadata['user_id'],
                "username": metadata['username'],
                "room_id": metadata['room_id'],
                "mime_type": metadata['mime_type'],
                "timestamp": datetime.now().timestamp(),
                "file_data_b64": base64.b64encode(file_data).decode('utf-8')  # Incluir dados para distribuição
            }
            
            # Limpar upload da memória
            del self.file_uploads[file_id]
            
            return result
        
        except grpc.RpcError as e:
            logger.error(f"❌ Erro ao enviar arquivo para Module B: {e.details()}")
            upload["status"] = "error"
            return {
                "success": False,
                "error": f"Erro ao enviar para Module B: {e.details()}",
                "file_id": file_id
            }
        except Exception as e:
            logger.error(f"❌ Erro ao processar arquivo: {str(e)}")
            upload["status"] = "error"
            return {
                "success": False,
                "error": f"Erro ao processar arquivo: {str(e)}",
                "file_id": file_id
            }


    def get_online_users(self, room_id: str) -> List[Dict[str, Any]]:
        """
        Obtém lista de usuários online via Module A (UserService)
        """
        try:
            channel = grpc.insecure_channel(f'{self.modulo_a_host}:{self.modulo_a_port}')
            stub = servico_pb2_grpc.UserServiceStub(channel)
            
            request = servico_pb2.OnlineUsersRequest(room_id=room_id)
            response = stub.GetOnlineUsers(request, timeout=10)
            channel.close()
            
            users = []
            for user_info in response.users:
                users.append({
                    "user_id": user_info.user_id,
                    "username": user_info.username,
                    "status": user_info.status,
                    "last_seen": user_info.last_seen
                })
            
            logger.info(f"✅ Obtidos {len(users)} usuários online de Module A")
            return users
        except Exception as e:
            logger.error(f"❌ Erro ao obter usuários do Module A: {str(e)}")
            return []

    
    def login_user(self, username: str, room_id: str) -> Dict[str, Any]:
        """
        Faz login do usuário via Module A (UserService.LoginUser)
        """
        try:
            channel = grpc.insecure_channel(f'{self.modulo_a_host}:{self.modulo_a_port}')
            stub = servico_pb2_grpc.UserServiceStub(channel)
            
            request = servico_pb2.LoginRequest(
                username=username,
                room_id=room_id
            )
            
            response = stub.LoginUser(request, timeout=10)
            channel.close()
            
            logger.info(f"✅ Usuário {username} fez login no Module A")
            
            return {
                "success": response.success,
                "user_id": response.user_id,
                "username": response.username,
                "room_id": room_id,
                "message": response.message
            }
        except Exception as e:
            logger.error(f"❌ Erro ao fazer login no Module A: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Erro ao fazer login: {str(e)}")

# Instância global do cliente de chat
chat_client = GrpcChatClient()

# Instância global do cliente (padrão: gRPC)
service_client = ServiceClient(modo=os.getenv('MODOP_COMUNICACAO', 'grpc'))

@app.on_event("startup")
async def startup_event():
    print("🚀 Módulo P (Gateway) iniciado!")
    print(f"📡 Modo de comunicação: {service_client.modo.upper()}")
    print("📨 Integração com Module A ativada para processamento de mensagens")

@app.on_event("shutdown")
async def shutdown_event():
    print("🔌 Fechando conexões...")
    service_client.close_connections()

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
    Agora suporta comunicação via gRPC ou REST/JSON (definido por variável de ambiente MODOP_COMUNICACAO)
    """
    print(f"📨 Recebida requisição: {request.id}")
    try:
        print(f"🔄 Chamando Módulo A para ID: {request.id}")
        resultado_a = service_client.chamar_servico_a(request)
        print(f"🔄 Chamando Módulo B para ID: {request.id}")
        resultados_b = service_client.chamar_servico_b(request, resultado_a.get("resultado", resultado_a.get("result", "")))
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
        "service": "Módulo P - Chat Gateway",
        "version": "2.0.0",
        "features": ["http", "websocket", "grpc", "chat"]
    }

# ================================
# CHAT ENDPOINTS
# ================================

def create_grpc_chat_stream(room_id: str):
    """
    Cria um gerador que implementa a interface do ChatStream do gRPC.
    Isso permite enviar mensagens para o Module A via bidirectional streaming.
    """
    # Esta é uma fila que será preenchida conforme mensagens chegam
    pass  # Será implementado com mais detalhes

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, username: str = None):
    """
    WebSocket endpoint para chat em tempo real
    Integração com Module A para processamento de mensagens via gRPC
    Parâmetros:
    - room_id: ID da sala de chat
    - username: Nome do usuário (query parameter)
    
    FLUXO DE MENSAGENS:
    1. Cliente envia mensagem via WebSocket
    2. Module P recebe a mensagem
    3. Module P envia para Module A processar (gRPC)
    4. Module A processa e retorna
    5. Module P distribui a mensagem processada para outros usuários
    """
    if not username:
        await websocket.close(code=4000, reason="Username is required")
        return
    
    # Gerar ID único para o usuário
    user_id = str(uuid.uuid4())
    
    try:
        await manager.connect(websocket, user_id, username, room_id)
        
        while True:
            # Recebe mensagens do cliente WebSocket
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type", "MESSAGE")
            content = message_data.get("content", "")
            
            # ========================================
            # INTEGRAÇÃO COM MODULE A - Processamento de Mensagens
            # ========================================
            # INTEGRAÇÃO COM MODULE B - Processamento de Arquivos
            # ========================================
            if message_type == "FILE_CHUNK":
                file_id = message_data.get("file_id")
                chunk_index = message_data.get("chunk_index", 0)
                total_chunks = message_data.get("total_chunks", 0)
                chunk_data_b64 = message_data.get("chunk_data", "")
                filename = message_data.get("filename", "")
                
                # Iniciar upload se for o primeiro chunk
                if chunk_index == 0:
                    chat_client.start_file_upload(
                        file_id=file_id,
                        filename=filename,
                        mime_type=message_data.get("mime_type", "application/octet-stream"),
                        file_size=message_data.get("file_size", 0),
                        user_id=user_id,
                        username=username,
                        room_id=room_id
                    )
                
                # Decodificar base64 e adicionar chunk
                try:
                    import base64
                    chunk_data = base64.b64decode(chunk_data_b64)
                    chat_client.add_file_chunk(file_id, chunk_data, chunk_index, total_chunks)
                    logger.info(f"📥 Chunk {chunk_index + 1}/{total_chunks} de {filename} recebido")
                except Exception as e:
                    logger.error(f"❌ Erro ao processar chunk: {str(e)}")
                
                # IMPORTANTE: Continue para pular o processamento de MESSAGE abaixo
                continue
            
            elif message_type == "FILE_SHARE":
                file_id = message_data.get("file_id")
                logger.info(f"📎 Completando upload de arquivo: {file_id}")
                
                # Finalizar upload e enviar para Module B
                upload_result = chat_client.finalize_file_upload(file_id)
                
                if upload_result.get("success"):
                    logger.info(f"✅ Arquivo processado e enviado para Module B")
                    
                    # Criar mensagem de compartilhamento de arquivo
                    file_message = {
                        "message_id": str(uuid.uuid4()),
                        "file_id": upload_result.get("file_id"),
                        "filename": upload_result.get("filename"),
                        "file_size": upload_result.get("file_size"),
                        "mime_type": upload_result.get("mime_type"),
                        "user_id": user_id,
                        "username": username,
                        "timestamp": datetime.now().timestamp(),
                        "type": "FILE_SHARE",
                        "room_id": room_id,
                        "processed_by": "module_b"
                    }
                    
                    # Armazenar e fazer broadcast para TODOS os usuários na sala (incluindo o uploader)
                    manager.store_message(room_id, file_message)
                    await manager.broadcast_to_room(room_id, file_message)
                    
                    # Enviar dados do arquivo em chunks para todos os usuários (exceto uploader que já tem)
                    file_data_b64 = upload_result.get("file_data_b64", "")
                    if file_data_b64:
                        file_size = upload_result.get("file_size", 0)
                        chunk_size = 512 * 1024  # 512KB chunks para WebSocket
                        
                        # Calcular número de chunks
                        total_chunks = (len(file_data_b64) + chunk_size - 1) // chunk_size
                        
                        logger.info(f"📤 Enviando arquivo em {total_chunks} chunks via WebSocket")
                        
                        # Enviar cada chunk
                        for chunk_idx in range(total_chunks):
                            start = chunk_idx * chunk_size
                            end = min(start + chunk_size, len(file_data_b64))
                            chunk = file_data_b64[start:end]
                            
                            file_chunk_message = {
                                "type": "FILE_CHUNK",
                                "file_id": upload_result.get("file_id"),
                                "filename": upload_result.get("filename"),
                                "mime_type": upload_result.get("mime_type"),
                                "file_size": file_size,
                                "chunk_index": chunk_idx,
                                "total_chunks": total_chunks,
                                "chunk_data": chunk,
                                "room_id": room_id
                            }
                            
                            # Enviar para TODOS os usuários (para que receberem e armazenem)
                            await manager.broadcast_to_room(room_id, file_chunk_message)
                    
                    logger.info(f"📤 Arquivo distribuído para sala {room_id}")
                else:
                    logger.error(f"❌ Erro ao processar arquivo: {upload_result.get('error')}")
                    error_message = {
                        "type": "SYSTEM",
                        "content": f"Erro ao enviar arquivo: {upload_result.get('error')}",
                        "timestamp": datetime.now().timestamp(),
                        "room_id": room_id
                    }
                    await manager.send_personal_message(error_message, websocket)
                
                # IMPORTANTE: Continue para pular o processamento de MESSAGE abaixo
                continue
            
            # ========================================
            # INTEGRAÇÃO COM MODULE A - Processamento de Mensagens
            # ========================================
            elif message_type == "MESSAGE" and content:
                logger.info(f"📨 Mensagem recebida de {username}: {content[:50]}...")
                logger.info(f"🔄 Enviando para Module A processar...")
                
                # Processar mensagem via Module A
                process_result = chat_client.process_message(
                    username=username,
                    content=content,
                    room_id=room_id,
                    user_id=user_id
                )
                
                # Usar conteúdo processado por Module A
                processed_content = process_result.get("processed_content", content)
                
                logger.info(f"✅ Mensagem processada por Module A: {processed_content[:50]}...")
            else:
                processed_content = content
            
            # Criar mensagem estruturada com conteúdo processado
            if message_type == "MESSAGE":
                chat_message = {
                    "message_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "username": username,
                    "content": processed_content,  # Conteúdo processado por Module A
                    "original_content": content,  # Conteúdo original (para referência)
                    "timestamp": datetime.now().timestamp(),
                    "type": message_type,
                    "room_id": room_id,
                    "processed_by": "module_a"
                }
                
                # Armazenar mensagem em memória
                manager.store_message(room_id, chat_message)
                
                # Broadcast para todos os usuários da sala (exceto o remetente)
                await manager.broadcast_to_room(room_id, chat_message, exclude_user=user_id)
                
                logger.info(f"📤 Mensagem distribuída para sala {room_id}")
    except WebSocketDisconnect:
        username = manager.disconnect(user_id, room_id)
        if username:
            # Notificar outros usuários sobre a saída
            await manager.broadcast_to_room(room_id, {
                "type": "USER_LEAVE",
                "username": username,
                "user_id": user_id,
                "timestamp": datetime.now().timestamp(),
                "message": f"{username} saiu do chat"
            })
    except Exception as e:
        logger.error(f"❌ WebSocket error for user {username}: {e}")
        manager.disconnect(user_id, room_id)

@app.post("/api/chat/login")
async def chat_login(request: ChatLoginRequest):
    """
    Endpoint HTTP para validar login do usuário via Module A
    Integração com Module A: UserService.LoginUser()
    """
    try:
        # Chamar Module A para validar usuário
        channel_a = grpc.insecure_channel(
            f"{os.getenv('MODULO_A_HOST', 'localhost')}:{os.getenv('MODULO_A_PORT', '50051')}"
        )
        stub_a = servico_pb2_grpc.UserServiceStub(channel_a)
        
        # Enviar requisição para Module A fazer login
        login_request = servico_pb2.LoginRequest(
            username=request.username,
            room_id=request.room_id
        )
        
        response = stub_a.LoginUser(login_request, timeout=10)
        channel_a.close()
        
        return {
            "success": response.success,
            "user_id": response.user_id,
            "username": response.username,
            "room_id": response.room_id,
            "message": response.message
        }
    except grpc.RpcError as e:
        logger.error(f"Erro ao chamar Module A para login: {e.details()}")
        raise HTTPException(status_code=503, detail=f"Erro de autenticação: {e.details()}")
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no login: {str(e)}")

@app.get("/api/chat/rooms/{room_id}/users")
async def get_room_users(room_id: str):
    """
    Obter lista de usuários online em uma sala
    """
    try:
        users = []
        if room_id in manager.online_users:
            users = [
                {
                    "user_id": user_id,
                    "username": user_info["username"],
                    "status": user_info["status"],
                    "joined_at": user_info["joined_at"]
                }
                for user_id, user_info in manager.online_users[room_id].items()
            ]
        
        return {
            "room_id": room_id,
            "users": users,
            "total_count": len(users)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter usuários: {str(e)}")

@app.get("/api/chat/rooms/{room_id}/messages")
async def get_room_messages(room_id: str, limit: int = 50):
    """
    Obter histórico de mensagens de uma sala
    """
    try:
        messages = []
        if room_id in manager.message_history:
            messages = manager.message_history[room_id][-limit:]
        
        return {
            "room_id": room_id,
            "messages": messages,
            "total_count": len(messages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter mensagens: {str(e)}")

@app.post("/api/chat/rooms/{room_id}/message")
async def send_message_http(room_id: str, request: ChatMessageRequest):
    """
    Endpoint HTTP alternativo para enviar mensagens (para testes)
    Integração com Module A: ChatService.ChatStream() para bidirectional streaming
    """
    try:
        # Criar mensagem estruturada
        chat_message = {
            "message_id": str(uuid.uuid4()),
            "user_id": "http_user",
            "username": request.username,
            "content": request.content,
            "timestamp": datetime.now().timestamp(),
            "type": request.message_type,
            "room_id": room_id
        }
        
        # Armazenar e broadcast localmente (em produção, seria via Module A)
        manager.store_message(room_id, chat_message)
        await manager.broadcast_to_room(room_id, chat_message)
        
        return {
            "success": True,
            "message": "Mensagem enviada com sucesso",
            "message_id": chat_message["message_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar mensagem: {str(e)}")

# ================================
# FILE TRANSFER ENDPOINTS (Module B Integration)
# ================================

class FileUploadRequest(BaseModel):
    """Modelo para upload de arquivo"""
    filename: str
    room_id: str = "global"
    uploader_id: str
    file_size: int  # em bytes

@app.post("/api/files/upload")
async def upload_file(request: FileUploadRequest):
    """
    Endpoint para iniciar upload de arquivo via Module B
    Integração com Module B: FileService.UploadFile() (client-streaming)
    """
    try:
        if request.file_size > 25 * 1024 * 1024:  # 25MB limit
            raise HTTPException(status_code=413, detail="Arquivo muito grande (máx 25MB)")
        
        # Criar sessão de upload
        file_id = str(uuid.uuid4())
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": request.filename,
            "room_id": request.room_id,
            "upload_url": f"/api/files/upload/stream/{file_id}",
            "max_chunk_size": 1024 * 1024  # 1MB chunks
        }
    except Exception as e:
        logger.error(f"Erro ao iniciar upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar upload: {str(e)}")

@app.post("/api/files/upload/stream/{file_id}")
async def upload_file_chunk(file_id: str, chunk_data: bytes):
    """
    Endpoint para enviar chunks de arquivo para Module B
    Integração com Module B: FileService.UploadFile() streaming
    """
    try:
        # Aqui seria feita a chamada gRPC para Module B com o chunk
        # Por enquanto, apenas confirmamos o recebimento
        
        logger.info(f"Chunk recebido para arquivo {file_id}: {len(chunk_data)} bytes")
        
        return {
            "success": True,
            "file_id": file_id,
            "chunk_size": len(chunk_data)
        }
    except Exception as e:
        logger.error(f"Erro ao enviar chunk: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao enviar chunk: {str(e)}")

@app.get("/api/files/room/{room_id}")
async def get_room_files(room_id: str):
    """
    Endpoint para obter lista de arquivos disponíveis em uma sala
    Integração com Module B: FileService.ReceiveFiles() para listar arquivos
    """
    try:
        # Aqui seria feita a chamada gRPC para Module B para listar arquivos
        files_list = []
        
        return {
            "success": True,
            "room_id": room_id,
            "files": files_list,
            "total_count": len(files_list)
        }
    except Exception as e:
        logger.error(f"Erro ao obter arquivos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter arquivos: {str(e)}")

@app.get("/api/files/download/{file_id}")
async def download_file(file_id: str, room_id: str = "global"):
    """
    Endpoint para download de arquivo via Module B
    Integração com Module B: FileService.ReceiveFiles() (server-streaming)
    """
    try:
        # Aqui seria feita a chamada gRPC para Module B para fazer download
        
        return {
            "success": True,
            "message": "Download iniciado",
            "file_id": file_id
        }
    except Exception as e:
        logger.error(f"Erro ao fazer download: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao fazer download: {str(e)}")

# Servir arquivos estáticos (frontend)
@app.get("/")
async def serve_chat():
    """
    Endpoint para servir a página de chat
    """
    return {
        "message": "Chat Gateway está funcionando!",
        "websocket_url": "ws://localhost:8000/ws/global?username=YOUR_USERNAME",
        "api_docs": "http://localhost:8000/docs",
        "health": "http://localhost:8000/health"
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