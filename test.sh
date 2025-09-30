#!/bin/bash

# Script para testar o projeto distribuído

echo "🧪 Testando Projeto Distribuído"
echo "==============================="

# Verifica se o gateway está rodando
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Gateway não está acessível. Execute './start.sh' primeiro."
    exit 1
fi

echo "✅ Gateway está acessível"
echo ""

# Teste 1: Health Check
echo "🔍 Teste 1: Health Check"
response=$(curl -s http://localhost:8000/health)
echo "Resposta: $response"
echo ""

# Teste 2: Root endpoint
echo "🔍 Teste 2: Root Endpoint"
response=$(curl -s http://localhost:8000/)
echo "Resposta: $response"
echo ""

# Teste 3: Execução completa - Uppercase
echo "🔍 Teste 3: Execução Completa (Uppercase)"
echo "Enviando requisição para /api/executar..."

response=$(curl -s -X POST "http://localhost:8000/api/executar" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "teste-uppercase-001",
       "data": "hello_world",
       "operation": "uppercase",
       "count": 3
     }')

echo "Resposta:"
echo "$response" | python -m json.tool 2>/dev/null || echo "$response"
echo ""

# Teste 4: Execução completa - Reverse
echo "🔍 Teste 4: Execução Completa (Reverse)"
echo "Enviando requisição para /api/executar..."

response=$(curl -s -X POST "http://localhost:8000/api/executar" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "teste-reverse-002", 
       "data": "abcdef",
       "operation": "reverse",
       "count": 2
     }')

echo "Resposta:"
echo "$response" | python -m json.tool 2>/dev/null || echo "$response"
echo ""

# Teste 5: Execução completa - Length
echo "🔍 Teste 5: Execução Completa (Length)"
echo "Enviando requisição para /api/executar..."

response=$(curl -s -X POST "http://localhost:8000/api/executar" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "teste-length-003",
       "data": "projeto_distribuido_grpc",
       "operation": "length",
       "count": 5
     }')

echo "Resposta:"
echo "$response" | python -m json.tool 2>/dev/null || echo "$response"
echo ""

echo "✅ Testes concluídos!"
echo ""
echo "📊 Para monitorar logs dos serviços:"
echo "   docker-compose logs -f"