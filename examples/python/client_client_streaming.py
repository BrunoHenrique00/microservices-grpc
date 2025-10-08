import grpc
import servico_pb2
import servico_pb2_grpc


def request_generator():
    for i, part in enumerate(['p1','p2','p3'], start=1):
        yield servico_pb2.RequestC(id='req-3', data=part, part=i)


def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = servico_pb2_grpc.ServicoCStub(channel)
    resp = stub.RealizarTarefaC(request_generator())
    print('Final response:', resp)


if __name__ == '__main__':
    run()
