import threading
import time
from concurrent import futures

import grpc
import servico_pb2
import servico_pb2_grpc


class ServicoAServicerImpl(servico_pb2_grpc.ServicoAServicer):
    def RealizarTarefaA(self, request, context):
        result = request.data.upper() + "_PROCESSED"
        return servico_pb2.ResponseA(id=request.id, result=result, message="Processed by inline server", status_code=200)


def serve_server(stop_event):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    servico_pb2_grpc.add_ServicoAServicer_to_server(ServicoAServicerImpl(), server)
    server.add_insecure_port('127.0.0.1:50051')
    server.start()
    print('Inline mock server started on 127.0.0.1:50051')
    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        server.stop(0)
        print('Inline mock server stopped')


def run_client():
    channel = grpc.insecure_channel('127.0.0.1:50051')
    stub = servico_pb2_grpc.ServicoAStub(channel)
    req = servico_pb2.RequestA(id='test-inline', data='hello', operation='uppercase')
    resp = stub.RealizarTarefaA(req, timeout=5)
    print('Client response:', resp)


if __name__ == '__main__':
    stop_event = threading.Event()
    t = threading.Thread(target=serve_server, args=(stop_event,), daemon=True)
    t.start()
    time.sleep(0.5)
    try:
        run_client()
    except Exception as e:
        print('Client error:', e)
    finally:
        stop_event.set()
        t.join()
