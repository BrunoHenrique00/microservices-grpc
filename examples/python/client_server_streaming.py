import grpc
import servico_pb2
import servico_pb2_grpc


def run():
    channel = grpc.insecure_channel('localhost:50052')
    stub = servico_pb2_grpc.ServicoBStub(channel)
    req = servico_pb2.RequestB(id='req-2', data='hello_stream', count=3)
    for resp in stub.RealizarTarefaB(req):
        print('Partial response:', resp)


if __name__ == '__main__':
    run()
