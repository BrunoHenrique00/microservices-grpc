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
echo "🔨 Construindo e iniciando serviços de chat..."
echo "   - Módulo A (UserService + ChatService - porta 50051)"
echo "   - Módulo B (FileService - porta 50052)" 
echo "   - Módulo P (WebSocket Gateway - porta 8000)"
echo "   - Frontend (Chat Interface - porta 3000)"
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

# Verifica Módulo A (UserService + ChatService)
if docker compose ps modulo-a | grep -q "Up"; then
    echo "✅ Módulo A (UserService + ChatService): Running (porta 50051)"
else
    echo "❌ Módulo A: Failed"
    services_ok=false
fi

# Verifica Módulo B (FileService)
if docker compose ps modulo-b | grep -q "Up"; then
    echo "✅ Módulo B (FileService): Running (porta 50052)"
else
    echo "❌ Módulo B: Failed"
    services_ok=false
fi

# Verifica Módulo P (Gateway/WebSocket)
if docker compose ps modulo-p | grep -q "Up"; then
    echo "✅ Módulo P (WebSocket Gateway): Running (porta 8000)"
else
    echo "❌ Módulo P: Failed"
    services_ok=false
fi

# Verifica Frontend
if docker compose ps chat-frontend | grep -q "Up"; then
    echo "✅ Frontend (Chat Interface): Running (porta 3000)"
else
    echo "❌ Frontend: Failed"
    services_ok=false
fi

echo ""

if [ "$services_ok" = true ]; then
    echo "🎉 Sistema de Chat em Tempo Real está funcionando!"
    echo ""
    echo "📋 URLs disponíveis:"
    echo "   💬 Chat Interface: http://localhost:3000"
    echo "   🌐 WebSocket Gateway: http://localhost:8000"
    echo "   📖 API Documentation: http://localhost:8000/docs"
    echo "   💚 Health Check: http://localhost:8000/health"
    echo ""
    echo "🚀 Como usar o Chat:"
    echo "   1. Abra seu navegador em http://localhost:3000"
    echo "   2. Digite seu nome de usuário"
    echo "   3. Entre na sala 'global' ou crie uma nova"
    echo "   4. Comece a conversar em tempo real!"
    echo ""
    echo "🔧 Teste via WebSocket diretamente:"
    echo "   ws://localhost:8000/ws/global?username=SEU_NOME"
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