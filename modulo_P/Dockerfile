# Dockerfile para Módulo P (Python FastAPI)
FROM python:3.11-slim

# Instala curl para health checks e ferramentas de build necessárias
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos de requisitos
COPY modulo_P/requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia a pasta protos (necessária para gerar os stubs)
COPY protos ./protos

# Copia os arquivos do projeto
COPY modulo_P/ .

# Gera os stubs gRPC
RUN python generate_protos.py

# Cria um usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expõe a porta do FastAPI
EXPOSE 8000

# Comando para iniciar o servidor FastAPI
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]