#!/bin/bash

# Script para iniciar o projeto distribuído

echo "🚀 Iniciando Projeto Distribuído com gRPC"
echo "========================================"

# Verifica se o Docker Compose está disponível
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose não encontrado. Por favor, instale o Docker Compose."
    exit 1
fi

# Verifica se o Docker está rodando
if ! docker info &> /dev/null; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker."
    exit 1
fi

echo "✅ Pré-requisitos verificados"
echo ""

# Limpa containers anteriores se existirem
echo "🧹 Limpando containers anteriores..."
docker compose down 2>/dev/null

echo ""
echo "🔨 Construindo e iniciando serviços..."
echo "   - Módulo A (gRPC Server - porta 50051)"
echo "   - Módulo B (gRPC Server - porta 50052)" 
echo "   - Módulo P (Gateway HTTP - porta 8000)"
echo ""

# Inicia os serviços
docker compose up --build -d

echo ""
echo "⏳ Aguardando serviços ficarem prontos..."

# Aguarda os serviços ficarem saudáveis
sleep 10

# Verifica se os serviços estão rodando
echo ""
echo "🔍 Verificando status dos serviços..."

services_ok=true

# Verifica Módulo A
if docker compose ps modulo-a | grep -q "Up"; then
    echo "✅ Módulo A: Running (porta 50051)"
else
    echo "❌ Módulo A: Failed"
    services_ok=false
fi

# Verifica Módulo B
if docker compose ps modulo-b | grep -q "Up"; then
    echo "✅ Módulo B: Running (porta 50052)"
else
    echo "❌ Módulo B: Failed"
    services_ok=false
fi

# Verifica Módulo P
if docker compose ps modulo-p | grep -q "Up"; then
    echo "✅ Módulo P: Running (porta 8000)"
else
    echo "❌ Módulo P: Failed"
    services_ok=false
fi

echo ""

if [ "$services_ok" = true ]; then
    echo "🎉 Todos os serviços estão rodando com sucesso!"
    echo ""
    echo "📋 URLs disponíveis:"
    echo "   🌐 API Gateway: http://localhost:8000"
    echo "   📖 Documentação: http://localhost:8000/docs"
    echo "   💚 Health Check: http://localhost:8000/health"
    echo ""
    echo "🔧 Exemplo de uso:"
    echo "curl -X POST \"http://localhost:8000/api/executar\" \\"
    echo "     -H \"Content-Type: application/json\" \\"
    echo "     -d '{"
    echo "       \"id\": \"teste-001\","
    echo "       \"data\": \"hello_world\","
    echo "       \"operation\": \"uppercase\","
    echo "       \"count\": 3"
    echo "     }'"
    echo ""
    echo "📊 Para ver logs em tempo real:"
    echo "   docker compose logs -f"
    echo ""
    echo "🛑 Para parar os serviços:"
    echo "   docker compose down"
else
    echo "❌ Alguns serviços falharam ao iniciar."
    echo ""
    echo "🔍 Para investigar problemas:"
    echo "   docker compose logs"
    echo ""
    echo "🛑 Para parar e limpar:"
    echo "   docker compose down"
fi