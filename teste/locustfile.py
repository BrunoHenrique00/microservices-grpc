import time
import json
import random
from teste.locustfile import HttpUser, task, between, events
from geventwebsocket.exceptions import WebSocketError
from websocket import create_connection, WebSocketConnectionClosedException, WebSocketTimeoutException

# --- CONFIGURAÇÃO ---
# O Módulo P (WebSocket Gateway) está em http://localhost:8000
GATEWAY_HOST = "localhost:8000"
WEBSOCKET_URL = f"ws://{GATEWAY_HOST}/ws/chat"
HTTP_UPLOAD_URL = f"http://{GATEWAY_HOST}/upload-file" # Endereço de upload no Módulo P

# Conteúdo simulado para o upload de arquivo (Módulo B)
SIMULATED_FILE_DATA = b"x" * 1024 * 10 # 10KB de dados binários simulados (Teste de Carga Pesada)

class ChatUser(HttpUser):
    # Tempo de espera entre a execução de diferentes tarefas
    wait_time = between(5, 15)
    
    # O host principal do Locust para requisições HTTP (Módulo P)
    host = f"http://{GATEWAY_HOST}" 
    
    def on_start(self):
        """Executado quando o usuário virtual começa a rodar."""
        # 1. Login/Conexão WebSocket (Aciona Módulo P -> Módulo A)
        self.username = f"User_{random.randint(1000, 9999)}_{time.time()}"
        self.room = "teste" 
        self.ws = None
        self.connect_to_chat()
        
    def on_stop(self):
        """Executado quando o usuário virtual para de rodar."""
        if self.ws:
            self.ws.close()
            
    def connect_to_chat(self):
        """Simula a conexão inicial do WebSocket."""
        ws_url = f"{WEBSOCKET_URL}?username={self.username}&room_id={self.room}"
        
        try:
            start_time = time.time()
            self.ws = create_connection(ws_url, timeout=5)
            
            # Marca a conexão como bem-sucedida para o Locust
            events.request.fire(
                request_type="WebSocket",
                name="/ws/chat/connect",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                success=True
            )
        except Exception as e:
            self.ws = None
            events.request.fire(
                request_type="WebSocket",
                name="/ws/chat/connect",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                success=False,
                exception=e
            )

    @task(8) # Prioridade: 80%
    def send_text_message(self):
        """Simula o envio de uma mensagem de texto (Carga Média - Aciona Módulo A)."""
        if self.ws:
            try:
                message = f"Olá, testando a carga em {time.time()}."
                start_time = time.time()
                self.ws.send(message)
                
                # Para fins de Locust, consideramos o envio como a operação de rede
                events.request.fire(
                    request_type="WebSocket",
                    name="/ws/chat/send_text",
                    response_time=(time.time() - start_time) * 1000,
                    response_length=len(message),
                    success=True
                )
            except (WebSocketConnectionClosedException, WebSocketError) as e:
                events.request.fire(
                    request_type="WebSocket",
                    name="/ws/chat/send_text",
                    response_time=(time.time() - start_time) * 1000,
                    response_length=0,
                    success=False,
                    exception=e
                )

    @task(2) # Prioridade: 20%
    def upload_file(self):
        """Simula o upload de um arquivo (Carga Pesada - Aciona Módulo B)."""
        if self.ws:
            # 1. Simula o upload do arquivo via requisição HTTP (Módulo P)
            files = {'file': ('test-file.bin', SIMULATED_FILE_DATA, 'application/octet-stream')}
            
            with self.client.post(self.HTTP_UPLOAD_URL, files=files, name="/upload-file (POST)", catch_response=True) as response:
                if response.status_code == 200:
                    try:
                        # O Módulo P responde com o ID/Path do arquivo no Módulo B
                        file_info = response.json()
                        file_id = file_info.get("file_id")
                        
                        # 2. Envia a URL/ID do arquivo para o chat via WebSocket
                        message = json.dumps({"type": "file_uploaded", "file_id": file_id})
                        self.ws.send(message)
                        response.success() # Marca a transação HTTP/WS como sucesso
                        
                    except (json.JSONDecodeError, WebSocketError) as e:
                        response.failure(f"Upload OK, mas falha no WS/JSON: {e}")
                else:
                    response.failure(f"Falha no Upload HTTP: Status {response.status_code}")