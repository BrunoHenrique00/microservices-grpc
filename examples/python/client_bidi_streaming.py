import grpc
import servico_pb2
import servico_pb2_grpc
import time


def request_generator(out_messages):
    for i, m in enumerate(out_messages, start=1):
        yield servico_pb2.RequestD(id=f'req-4', data=m, sequence=i)
        time.sleep(0.2)


def run():
    channel = grpc.insecure_channel('localhost:50052')
    stub = servico_pb2_grpc.ServicoDStub(channel)
    out_messages = ['m1','m2','m3']
    responses = stub.RealizarTarefaD(request_generator(out_messages))
    for resp in responses:
        print('Bidi response:', resp)


if __name__ == '__main__':
    run()
