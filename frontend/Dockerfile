# Dockerfile para o Frontend (Node.js) com Chat HTML
FROM node:18-alpine

# Instalar dependências de sistema
RUN apk add --no-cache curl

WORKDIR /app

# Copiar arquivos de configuração do Node.js
COPY package*.json ./

# Instalar dependências
RUN npm install --production

# Copiar arquivos da aplicação
COPY . .

# Expor porta
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Iniciar servidor
CMD ["node", "server.js"]
