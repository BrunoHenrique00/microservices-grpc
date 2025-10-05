import threading
import time
from concurrent import futures

import grpc
import servico_pb2
import servico_pb2_grpc


class ServicoCServicerImpl(servico_pb2_grpc.ServicoCServicer):
    def RealizarTarefaC(self, request_iterator, context):
        parts = []
        for req in request_iterator:
            parts.append(req.data)
        summary = '|'.join(parts)
        return servico_pb2.ResponseC(id='resp-c', summary=summary, total_parts=len(parts), message='Aggregated')


def serve_server(stop_event):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    servico_pb2_grpc.add_ServicoCServicer_to_server(ServicoCServicerImpl(), server)
    server.add_insecure_port('127.0.0.1:50051')
    server.start()
    print('Inline mock ServicoC started on 127.0.0.1:50051')
    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        server.stop(0)
        print('Inline mock ServicoC stopped')


def run_client():
    channel = grpc.insecure_channel('127.0.0.1:50051')
    stub = servico_pb2_grpc.ServicoCStub(channel)

    def request_generator():
        for p in ['part1','part2','part3']:
            yield servico_pb2.RequestC(id='req-c', data=p, part=1)
            time.sleep(0.05)

    resp = stub.RealizarTarefaC(request_generator())
    print('Client final response:', resp)


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
