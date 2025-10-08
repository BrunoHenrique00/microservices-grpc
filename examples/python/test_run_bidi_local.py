import threading
import time
from concurrent import futures

import grpc
import servico_pb2
import servico_pb2_grpc


class ServicoDServicerImpl(servico_pb2_grpc.ServicoDServicer):
    def RealizarTarefaD(self, request_iterator, context):
        for req in request_iterator:
            # responde imediatamente ecoando o sequence
            yield servico_pb2.ResponseD(id=req.id, result=req.data.upper(), sequence=req.sequence, message='echo')


def serve_server(stop_event):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    servico_pb2_grpc.add_ServicoDServicer_to_server(ServicoDServicerImpl(), server)
    server.add_insecure_port('127.0.0.1:50052')
    server.start()
    print('Inline mock ServicoD started on 127.0.0.1:50052')
    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        server.stop(0)
        print('Inline mock ServicoD stopped')


def run_client():
    channel = grpc.insecure_channel('127.0.0.1:50052')
    stub = servico_pb2_grpc.ServicoDStub(channel)

    def request_generator():
        for i, m in enumerate(['hello','world','!'], start=1):
            yield servico_pb2.RequestD(id='req-d', data=m, sequence=i)
            time.sleep(0.05)

    for resp in stub.RealizarTarefaD(request_generator()):
        print('Client bidi received:', resp)


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
