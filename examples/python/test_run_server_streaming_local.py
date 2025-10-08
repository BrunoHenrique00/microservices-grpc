import threading
import time
from concurrent import futures

import grpc
import servico_pb2
import servico_pb2_grpc


class ServicoBServicerImpl(servico_pb2_grpc.ServicoBServicer):
    def RealizarTarefaB(self, request, context):
        # envia 'count' respostas no stream
        for i in range(1, max(1, request.count) + 1):
            resp = servico_pb2.ResponseB(
                id=request.id,
                result=f"{request.data}_part_{i}",
                message=f"Resposta {i} de {request.count}",
                sequence_number=i,
                is_final=(i == request.count)
            )
            yield resp
            time.sleep(0.1)


def serve_server(stop_event):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    servico_pb2_grpc.add_ServicoBServicer_to_server(ServicoBServicerImpl(), server)
    server.add_insecure_port('127.0.0.1:50052')
    server.start()
    print('Inline mock ServicoB started on 127.0.0.1:50052')
    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        server.stop(0)
        print('Inline mock ServicoB stopped')


def run_client():
    channel = grpc.insecure_channel('127.0.0.1:50052')
    stub = servico_pb2_grpc.ServicoBStub(channel)
    req = servico_pb2.RequestB(id='test-b', data='streamdata', count=3)
    for resp in stub.RealizarTarefaB(req):
        print('Client received:', resp)


if __name__ == '__main__':
    stop_event = threading.Event()
    t = threading.Thread(target=serve_server, args=(stop_event,), daemon=True)
    t.start()
    time.sleep(0.2)
    try:
        run_client()
    except Exception as e:
        print('Client error:', e)
    finally:
        stop_event.set()
        t.join()
