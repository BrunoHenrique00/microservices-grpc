#!/bin/bash

# Script para automatizar o deploy da aplicação distribuída no Minikube.
# Garante que os pré-requisitos estão instalados, constrói as imagens
# e aplica as configurações do Kubernetes.

# Sai imediatamente se um comando falhar
set -e

echo "🚀 Iniciando o Deploy no Kubernetes..."
echo "========================================"

# --- Verificação de Pré-requisitos ---
echo "1/5: Verificando pré-requisitos (minikube e docker)..."
if ! command -v minikube &> /dev/null; then
    echo "❌ Erro: Minikube não foi encontrado. Por favor, instale-o primeiro."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Erro: Docker não foi encontrado. Por favor, instale-o primeiro."
    exit 1
fi
echo "✅ Pré-requisitos OK."

# --- Iniciar o Minikube ---
echo -e "\n2/5: Iniciando o Minikube (pode demorar alguns minutos)..."
minikube start
echo "✅ Minikube iniciado."

# --- Conectar o Docker ao Minikube ---
echo -e "\n3/5: Conectando o ambiente Docker ao Minikube..."
eval $(minikube -p minikube docker-env)
echo "✅ Ambiente Docker configurado."

# --- Construir as Imagens Docker ---
echo -e "\n4/5: Construindo as imagens dos serviços..."
echo "   - Construindo imagem para o Módulo A..."
docker build -t modulo-a-grpc:latest -f modulo_A/Dockerfile .
echo "   - Construindo imagem para o Módulo B..."
docker build -t modulo-b-grpc:latest -f modulo_B/Dockerfile .
echo "   - Construindo imagem para o Módulo P (Gateway)..."
docker build -t modulo-p-gateway:latest -f modulo_P/Dockerfile .
echo "✅ Imagens construídas com sucesso."

# --- Aplicar as Configurações do Kubernetes ---
echo -e "\n5/5: Aplicando os manifestos do Kubernetes..."
# Aplica o namespace primeiro para evitar a race condition
minikube kubectl -- apply -f kubernetes/01-namespace.yaml

# Aguarda um momento para o namespace ser totalmente provisionado
sleep 2 

# Aplica o restante das configurações
minikube kubectl -- apply -f kubernetes/
echo "✅ Manifestos aplicados."

# --- Verificação Final ---
echo -e "\n⏳ Aguardando todos os pods ficarem no estado 'Running'..."
minikube kubectl -- wait --for=condition=ready pod --all -n projeto-distribuido --timeout=300s

echo -e "\n🎉 Deploy concluído com sucesso!"
echo "========================================"
echo "Sua aplicação distribuída está no ar."
echo ""
echo "Para acessar o Gateway, execute o seguinte comando em um novo terminal:"
echo "minikube service modulo-p-service -n projeto-distribuido"
echo ""
echo "Para ver o status de todos os recursos, execute:"
echo "minikube kubectl -- get all -n projeto-distribuido"
echo ""
echo "Para parar o cluster e liberar os recursos do seu PC, execute:"
echo "minikube stop"