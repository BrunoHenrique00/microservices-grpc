# Dockerfile para Módulo B (Node.js)
FROM node:18-alpine

# Instala netcat para health checks
RUN apk add --no-cache netcat-openbsd

# Define o diretório de trabalho
WORKDIR /app

# Copia a pasta protos (necessária para os stubs gRPC)
COPY protos ./protos

# Copia os arquivos de dependências
COPY modulo_B/package*.json ./

# Instala as dependências
RUN npm i 

# Copia o código fonte do módulo B
COPY modulo_B/ .

# Cria um usuário não-root para segurança
RUN addgroup -g 1001 -S nodejs && \
    adduser -S grpcuser -u 1001 -G nodejs

# Muda a propriedade dos arquivos para o usuário nodejs
RUN chown -R grpcuser:nodejs /app
USER grpcuser

# Expõe a porta do serviço gRPC
EXPOSE 50052

# Comando para iniciar o servidor
CMD ["node", "server.js"]