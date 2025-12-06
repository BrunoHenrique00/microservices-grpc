"""
Script para gerar os stubs Python a partir do arquivo .proto
Execute este script antes de iniciar o módulo P
"""

import subprocess
import sys
import os

def generate_grpc_stubs():
    """Gera os stubs gRPC Python a partir do arquivo .proto"""
    
    # Caminho para o arquivo .proto (dentro do container)
    proto_path = "./protos"
    proto_file = "servico.proto"
    
    # Diretório de saída para os stubs gerados
    output_dir = "."
    
    print("🔧 Gerando stubs gRPC Python...")

    # Verifica se o diretório e o arquivo .proto existem
    proto_dir_full = os.path.abspath(proto_path)
    proto_file_full = os.path.join(proto_dir_full, proto_file)
    if not os.path.isfile(proto_file_full):
        print(f"❌ Arquivo .proto não encontrado: {proto_file_full}")
        sys.exit(1)
    
    try:
        # Comando para gerar os stubs
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--proto_path={proto_path}",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
            os.path.join(proto_path, proto_file)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ Stubs gRPC gerados com sucesso!")
        print("📁 Arquivos gerados:")
        print("   - servico_pb2.py (mensagens protobuf)")
        print("   - servico_pb2_grpc.py (serviços gRPC)")
        print("")
        print("🎯 Serviços disponíveis:")
        print("   - ServicoA: Processamento unary")
        print("   - ServicoB: Streaming server-side")
        print("   - UserService: Gestão de usuários")
        print("   - ChatService: Chat em tempo real")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao gerar stubs: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ grpc_tools não encontrado. Instale com: pip install grpcio-tools")
        sys.exit(1)

if __name__ == "__main__":
    generate_grpc_stubs()