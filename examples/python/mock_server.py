import time
from concurrent import futures
import grpc
import servico_pb2
import servico_pb2_grpc


class ServicoAServicer(servico_pb2_grpc.ServicoAServicer):
    def RealizarTarefaA(self, request, context):
        # Simples processamento de exemplo
        result = request.data.upper() + "_PROCESSED"
        return servico_pb2.ResponseA(id=request.id, result=result, message="Processed by mock server", status_code=200)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    servico_pb2_grpc.add_ServicoAServicer_to_server(ServicoAServicer(), server)
    # Bind explicitly to IPv4 localhost to avoid IPv6/IPv4 issues on Windows
    bind_addr = '127.0.0.1:50051'
    server.add_insecure_port(bind_addr)
    server.start()
    print(f'Mock ServicoA started on {bind_addr}')
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
