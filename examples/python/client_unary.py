import grpc
import servico_pb2
import servico_pb2_grpc


def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = servico_pb2_grpc.ServicoAStub(channel)
    req = servico_pb2.RequestA(id='req-1', data='hello', operation='uppercase')
    resp = stub.RealizarTarefaA(req)
    print('Response:', resp)


if __name__ == '__main__':
    run()
