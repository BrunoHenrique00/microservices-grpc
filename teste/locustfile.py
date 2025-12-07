import time
import json
import random
import uuid
from locust import HttpUser, task, between, events
from geventwebsocket.exceptions import WebSocketError
from websocket import create_connection, WebSocketConnectionClosedException, WebSocketTimeoutException

# --- CONFIGURAÇÃO ---
# O Módulo P (WebSocket Gateway) está em http://localhost:8000
GATEWAY_HOST = "localhost:8000"
WEBSOCKET_URL = f"ws://{GATEWAY_HOST}/ws/chat"
HTTP_BASE_URL = f"http://{GATEWAY_HOST}"

# Conteúdo simulado para o upload de arquivo (Módulo B)
SIMULATED_FILE_DATA = b"x" * 1024 * 10  # 10KB de dados binários simulados

class ChatUser(HttpUser):
    # Tempo de espera entre a execução de diferentes tarefas (reduzido para mais requisições)
    wait_time = between(1, 3)
    
    # O host principal do Locust para requisições HTTP (Módulo P)
    host = HTTP_BASE_URL
    
    def on_start(self):
        """Executado quando o usuário virtual começa a rodar."""
        # 1. Login via HTTP (Gera requisição HTTP real)
        self.username = f"User_{random.randint(1000, 9999)}_{int(time.time() * 1000) % 10000}"
        self.room_id = random.choice(["chat", "teste", "geral", "tech"])
        self.user_id = str(uuid.uuid4())
        self.ws = None
        
        # Fazer login HTTP primeiro
        self.http_login()
        
        # Depois conectar via WebSocket
        self.connect_to_chat()
        
    def on_stop(self):
        """Executado quando o usuário virtual para de rodar."""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
    
    def http_login(self):
        """Faz login via HTTP (requisição real)."""
        try:
            response = self.client.post(
                "/api/chat/login",
                json={
                    "username": self.username,
                    "room_id": self.room_id
                },
                name="/api/chat/login"
            )
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get("user_id", self.user_id)
        except Exception as e:
            print(f"Erro no login HTTP: {e}")
            
    def connect_to_chat(self):
        """Simula a conexão inicial do WebSocket."""
        ws_url = f"{WEBSOCKET_URL}/{self.room_id}?username={self.username}"
        
        try:
            start_time = time.time()
            self.ws = create_connection(ws_url, timeout=5)
            
            # Marca a conexão como bem-sucedida para o Locust
            events.request.fire(
                request_type="WebSocket",
                name="/ws/{room_id}/connect",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                success=True
            )
        except Exception as e:
            self.ws = None
            events.request.fire(
                request_type="WebSocket",
                name="/ws/{room_id}/connect",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                success=False,
                exception=e
            )

    @task(15)  # Prioridade: 50% - Requisições HTTP frequentes
    def get_online_users(self):
        """Busca usuários online (requisição HTTP real)."""
        try:
            self.client.get(
                f"/api/chat/rooms/{self.room_id}/users",
                name="/api/chat/rooms/{room_id}/users"
            )
        except Exception as e:
            print(f"Erro ao buscar usuários: {e}")

    @task(15)  # Prioridade: 50% - Requisições HTTP frequentes
    def get_room_messages(self):
        """Busca mensagens da sala (requisição HTTP real)."""
        try:
            self.client.get(
                f"/api/chat/rooms/{self.room_id}/messages?limit=20",
                name="/api/chat/rooms/{room_id}/messages"
            )
        except Exception as e:
            print(f"Erro ao buscar mensagens: {e}")

    @task(20)  # Prioridade: 33% - Envio de mensagens via HTTP
    def send_message_http(self):
        """Envia mensagem via HTTP POST (requisição real)."""
        try:
            message_content = f"Mensagem teste {int(time.time() * 1000) % 10000}"
            self.client.post(
                f"/api/chat/rooms/{self.room_id}/message",
                json={
                    "username": self.username,
                    "content": message_content,
                    "room_id": self.room_id,
                    "message_type": "MESSAGE"
                },
                name="/api/chat/rooms/{room_id}/message"
            )
        except Exception as e:
            print(f"Erro ao enviar mensagem HTTP: {e}")

    @task(30)  # Prioridade: 30% - Envio de mensagens via WebSocket (mais frequente)
    def send_websocket_message(self):
        """Simula o envio de uma mensagem de texto via WebSocket (Carga Média)."""
        if self.ws:
            try:
                message = {
                    "type": "MESSAGE",
                    "content": f"WebSocket msg {int(time.time() * 1000) % 10000}",
                    "username": self.username
                }
                start_time = time.time()
                self.ws.send(json.dumps(message))
                
                # Registrar métrica
                events.request.fire(
                    request_type="WebSocket",
                    name="/ws/{room_id}/send_message",
                    response_time=(time.time() - start_time) * 1000,
                    response_length=len(json.dumps(message)),
                    success=True
                )
            except (WebSocketConnectionClosedException, WebSocketError) as e:
                events.request.fire(
                    request_type="WebSocket",
                    name="/ws/{room_id}/send_message",
                    response_time=0,
                    response_length=0,
                    success=False,
                    exception=e
                )
                # Tentar reconectar
                self.connect_to_chat()

    @task(10)  # Prioridade: 10% - Health check
    def health_check(self):
        """Verifica saúde do serviço (requisição HTTP real)."""
        try:
            self.client.get(
                "/health",
                name="/health"
            )
        except Exception as e:
            print(f"Erro no health check: {e}")
