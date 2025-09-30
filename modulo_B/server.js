/**
 * Módulo B - Servidor gRPC em Node.js
 * Implementa o ServicoB com método server-streaming RealizarTarefaB
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
 * Implementação do serviço B
 * Método server-streaming que retorna múltiplas respostas ao longo do tempo
 */
class ServicoBImpl {
  /**
   * Implementa o método RealizarTarefaB (server-streaming)
   * @param {Object} call - Objeto da chamada gRPC contendo a requisição e o stream
   */
  realizarTarefaB(call) {
    const request = call.request;

    console.log(`📨 [ServicoB] Recebida requisição para streaming:`);
    console.log(`   ID: ${request.id}`);
    console.log(`   Data: ${request.data}`);
    console.log(`   Count: ${request.count}`);

    try {
      // Valida o número de respostas solicitadas
      const responseCount = Math.min(Math.max(request.count || 3, 1), 10); // Entre 1 e 10

      console.log(
        `🔄 [ServicoB] Iniciando stream com ${responseCount} respostas`,
      );

      // Processa e envia respostas em intervalos
      this.enviarRespostasStream(call, request, responseCount);
    } catch (error) {
      console.error(`❌ [ServicoB] Erro no processamento:`, error);
      call.emit("error", {
        code: grpc.status.INTERNAL,
        details: `Erro no processamento: ${error.message}`,
      });
    }
  }

  /**
   * Envia respostas através do stream com intervalos de tempo
   * @param {Object} call - Objeto da chamada gRPC
   * @param {Object} request - Requisição original
   * @param {number} count - Número de respostas a enviar
   */
  async enviarRespostasStream(call, request, count) {
    for (let i = 1; i <= count; i++) {
      // Simula processamento com delay
      await this.delay(1000); // 1 segundo entre respostas

      // Verifica se o cliente ainda está conectado
      if (call.cancelled) {
        console.log(
          `🚫 [ServicoB] Stream cancelado pelo cliente para ID: ${request.id}`,
        );
        return;
      }

      // Processa dados para esta iteração
      const processedData = this.processarDadosStream(request.data, i, count);

      // Prepara a resposta
      const response = {
        id: request.id,
        result: processedData,
        message: `Resposta ${i} de ${count} do ServicoB`,
        sequence_number: i,
        is_final: i === count,
      };

      console.log(
        `📤 [ServicoB] Enviando resposta ${i}/${count} para ID: ${request.id}`,
      );

      // Envia a resposta através do stream
      call.write(response);

      // Se for a última resposta, finaliza o stream
      if (i === count) {
        console.log(`✅ [ServicoB] Stream finalizado para ID: ${request.id}`);
        call.end();
      }
    }
  }

  /**
   * Processa dados para cada resposta do stream
   * @param {string} data - Dados originais
   * @param {number} sequencia - Número da sequência atual
   * @param {number} total - Total de respostas
   * @returns {string} - Dados processados
   */
  processarDadosStream(data, sequencia, total) {
    const timestamp = new Date().toISOString();
    const progresso = ((sequencia / total) * 100).toFixed(1);

    // Diferentes tipos de processamento baseados na sequência
    const processamentos = [
      () => `${data}_chunk_${sequencia}_analyzed`,
      () => `${data}_chunk_${sequencia}_transformed`,
      () => `${data}_chunk_${sequencia}_enriched`,
      () => `${data}_chunk_${sequencia}_validated`,
      () => `${data}_chunk_${sequencia}_finalized`,
    ];

    const processador = processamentos[(sequencia - 1) % processamentos.length];
    const resultado = processador();

    return `${resultado}_progress_${progresso}%_at_${timestamp}`;
  }

  /**
   * Função utilitária para criar delays
   * @param {number} ms - Milissegundos para aguardar
   * @returns {Promise} - Promise que resolve após o delay
   */
  delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

/**
 * Função para iniciar o servidor gRPC
 */
function startServer() {
  const server = new grpc.Server();

  // Adiciona o serviço ao servidor
  server.addService(servicoProto.ServicoB.service, new ServicoBImpl());

  // Configuração do endereço e porta
  const serverAddress = "0.0.0.0:50052";

  // Bind do servidor na porta
  server.bindAsync(
    serverAddress,
    grpc.ServerCredentials.createInsecure(),
    (error, port) => {
      if (error) {
        console.error("❌ Erro ao iniciar servidor:", error);
        return;
      }

      console.log("🚀 Módulo B - Servidor gRPC iniciado!");
      console.log(`📍 Servidor rodando em: ${serverAddress}`);
      console.log(`🔧 Porta atribuída: ${port}`);
      console.log("🎯 Serviços disponíveis:");
      console.log("   - ServicoB.RealizarTarefaB (método server-streaming)");
      console.log("");
      console.log("⚡ Aguardando requisições de streaming...");

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
  console.log("🔧 Inicializando Módulo B...");
  startServer();
}

module.exports = { ServicoBImpl, startServer };
