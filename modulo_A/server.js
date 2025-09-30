/**
 * Módulo A - Servidor gRPC em Node.js
 * Implementa o ServicoA com método unary RealizarTarefaA
 */

const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");
const path = require("path");

// Configuração para carregar o arquivo .proto
const PROTO_PATH = path.join(__dirname, "protos", "servico.proto");

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});

// Carrega o package gRPC
const servicoProto = grpc.loadPackageDefinition(packageDefinition).servicoapp;

/**
 * Implementação do serviço A
 * Método unary que processa uma requisição e retorna uma resposta
 */
class ServicoAImpl {
  /**
   * Implementa o método RealizarTarefaA
   * @param {Object} call - Objeto da chamada gRPC contendo a requisição
   * @param {Function} callback - Callback para retornar a resposta
   */
  realizarTarefaA(call, callback) {
    const request = call.request;

    console.log(`📨 [ServicoA] Recebida requisição:`);
    console.log(`   ID: ${request.id}`);
    console.log(`   Data: ${request.data}`);
    console.log(`   Operation: ${request.operation}`);

    try {
      // Simula processamento da tarefa
      const processedData = this.processarDados(
        request.data,
        request.operation,
      );

      // Prepara a resposta
      const response = {
        id: request.id,
        result: processedData,
        message: `Tarefa A executada com sucesso para ID ${request.id}`,
        status_code: 200,
      };

      console.log(
        `✅ [ServicoA] Processamento concluído para ID: ${request.id}`,
      );
      console.log(`   Resultado: ${response.result}`);

      // Retorna a resposta via callback
      callback(null, response);
    } catch (error) {
      console.error(`❌ [ServicoA] Erro no processamento:`, error);

      // Retorna erro via callback
      const errorResponse = {
        id: request.id,
        result: "",
        message: `Erro no processamento: ${error.message}`,
        status_code: 500,
      };

      callback(null, errorResponse);
    }
  }

  /**
   * Processa os dados de acordo com a operação solicitada
   * @param {string} data - Dados para processar
   * @param {string} operation - Tipo de operação
   * @returns {string} - Dados processados
   */
  processarDados(data, operation) {
    const timestamp = new Date().toISOString();

    switch (operation) {
      case "uppercase":
        return `${data.toUpperCase()}_PROCESSED_AT_${timestamp}`;

      case "lowercase":
        return `${data.toLowerCase()}_processed_at_${timestamp}`;

      case "reverse":
        return `${data.split("").reverse().join("")}_processed_at_${timestamp}`;

      case "length":
        return `length_${data.length}_processed_at_${timestamp}`;

      default:
        return `${data}_default_processed_by_moduleA_at_${timestamp}`;
    }
  }
}

/**
 * Função para iniciar o servidor gRPC
 */
function startServer() {
  const server = new grpc.Server();

  // Adiciona o serviço ao servidor
  server.addService(servicoProto.ServicoA.service, new ServicoAImpl());

  // Configuração do endereço e porta
  const serverAddress = "0.0.0.0:50051";

  // Bind do servidor na porta
  server.bindAsync(
    serverAddress,
    grpc.ServerCredentials.createInsecure(),
    (error, port) => {
      if (error) {
        console.error("❌ Erro ao iniciar servidor:", error);
        return;
      }

      console.log("🚀 Módulo A - Servidor gRPC iniciado!");
      console.log(`📍 Servidor rodando em: ${serverAddress}`);
      console.log(`🔧 Porta atribuída: ${port}`);
      console.log("🎯 Serviços disponíveis:");
      console.log("   - ServicoA.RealizarTarefaA (método unary)");
      console.log("");
      console.log("⚡ Aguardando requisições...");

      // Inicia o servidor
      server.start();
    },
  );

  // Graceful shutdown
  process.on("SIGINT", () => {
    console.log("\n🔄 Recebido sinal SIGINT, encerrando servidor...");
    server.tryShutdown(() => {
      console.log("✅ Servidor encerrado graciosamente");
      process.exit(0);
    });
  });

  process.on("SIGTERM", () => {
    console.log("\n🔄 Recebido sinal SIGTERM, encerrando servidor...");
    server.tryShutdown(() => {
      console.log("✅ Servidor encerrado graciosamente");
      process.exit(0);
    });
  });
}

// Inicia o servidor se este arquivo for executado diretamente
if (require.main === module) {
  console.log("🔧 Inicializando Módulo A...");
  startServer();
}

module.exports = { ServicoAImpl, startServer };
