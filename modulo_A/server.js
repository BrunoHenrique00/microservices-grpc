/**
 * Módulo A - Servidor gRPC em Node.js
 * Implementa o ServicoA com método unary RealizarTarefaA
 * E o UserService para gestão de usuários do chat
 */

require("./metrics");
import("./metrics");

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
   * Mapa para contagem de palavras mais faladas
   */
  palavraContagem = new Map();

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

      case "process_message": {
        // Processamento especial para mensagens de chat
        // Exemplos de processamento:
        // - Remover espaços em branco desnecessários
        // - Converter URLs para links
        // - Remover palavras-chave proibidas
        // - Adicionar emojis de contexto

        const cleanedMessage = data
          .trim()
          .replace(/\s+/g, " ") // Normalizar espaços
          .replace(/^[!@#$%^&*]+/, ""); // Remover caracteres especiais no início

        // Contagem de palavras
        const palavras = cleanedMessage
          .toLowerCase()
          .replace(/[^\wÀ-ÿ ]+/g, "") // Remove pontuação
          .split(" ")
          .filter(Boolean);

        for (const palavra of palavras) {
          const atual = this.palavraContagem.get(palavra) || 0;
          this.palavraContagem.set(palavra, atual + 1);
        }

        // Log das 3 palavras mais faladas
        const topPalavras = Array.from(this.palavraContagem.entries())
          .sort((a, b) => b[1] - a[1])
          .slice(0, 3);
        console.log(
          `📊 Top 3 palavras mais faladas: ` +
            topPalavras.map(([p, c]) => `${p} (${c})`).join(", "),
        );

        // Exemplo: Adicionar timestamp de processamento
        return `${cleanedMessage}`;
      }

      default:
        return `${data}_default_processed_by_moduleA_at_${timestamp}`;
    }
  }
}

/**
 * Implementação do serviço de usuários
 * Gerencia operações de login, usuários online e status
 */
class UserServiceImpl {
  constructor() {
    // Armazenamento em memória dos usuários {user_id: user_info}
    this.users = new Map();
    // Usuários online por sala {room_id: Set(user_ids)}
    this.onlineUsers = new Map();
    // Cache de usernames para evitar duplicatas {room_id: Set(usernames)}
    this.usernameCache = new Map();
  }

  /**
   * Login/registro de usuário
   * @param {Object} call - Objeto da chamada gRPC
   * @param {Function} callback - Callback para retornar a resposta
   */
  loginUser(call, callback) {
    const request = call.request;
    const { username, room_id = "global" } = request;

    console.log(`📝 [UserService] Login request:`);
    console.log(`   Username: ${username}`);
    console.log(`   Room ID: ${room_id}`);

    try {
      // Validar entrada
      if (!username || username.trim().length === 0) {
        const errorResponse = {
          user_id: "",
          username: "",
          success: false,
          message: "Username é obrigatório",
          timestamp: Date.now(),
        };
        callback(null, errorResponse);
        return;
      }

      const cleanUsername = username.trim();

      // Verificar se o username já está em uso na sala
      if (!this.usernameCache.has(room_id)) {
        this.usernameCache.set(room_id, new Set());
      }

      if (this.usernameCache.get(room_id).has(cleanUsername)) {
        const errorResponse = {
          user_id: "",
          username: cleanUsername,
          success: false,
          message: `Username '${cleanUsername}' já está em uso nesta sala`,
          timestamp: Date.now(),
        };
        callback(null, errorResponse);
        return;
      }

      // Gerar ID único para o usuário
      const user_id = `user_${Date.now()}_${Math.random()
        .toString(36)
        .substring(2)}`;

      // Registrar usuário
      const userInfo = {
        user_id,
        username: cleanUsername,
        room_id,
        status: "ONLINE",
        joined_at: Date.now(),
        last_seen: Date.now(),
      };

      this.users.set(user_id, userInfo);
      this.usernameCache.get(room_id).add(cleanUsername);

      // Adicionar à lista de usuários online
      if (!this.onlineUsers.has(room_id)) {
        this.onlineUsers.set(room_id, new Set());
      }
      this.onlineUsers.get(room_id).add(user_id);

      console.log(
        `✅ [UserService] User ${cleanUsername} logged in successfully`,
      );
      console.log(`   User ID: ${user_id}`);
      console.log(`   Room: ${room_id}`);

      const response = {
        user_id,
        username: cleanUsername,
        success: true,
        message: `Usuário ${cleanUsername} autenticado com sucesso`,
        timestamp: Date.now(),
      };

      callback(null, response);
    } catch (error) {
      console.error(`❌ [UserService] Erro no login:`, error);

      const errorResponse = {
        user_id: "",
        username: username || "",
        success: false,
        message: `Erro interno no servidor: ${error.message}`,
        timestamp: Date.now(),
      };

      callback(null, errorResponse);
    }
  }

  /**
   * Obter lista de usuários online
   * @param {Object} call - Objeto da chamada gRPC
   * @param {Function} callback - Callback para retornar a resposta
   */
  getOnlineUsers(call, callback) {
    const request = call.request;
    const { room_id = "global" } = request;

    console.log(`👥 [UserService] Getting online users for room: ${room_id}`);

    try {
      const users = [];

      if (this.onlineUsers.has(room_id)) {
        const onlineUserIds = this.onlineUsers.get(room_id);

        for (const user_id of onlineUserIds) {
          const userInfo = this.users.get(user_id);
          if (userInfo) {
            users.push({
              user_id: userInfo.user_id,
              username: userInfo.username,
              status: userInfo.status,
              last_seen: userInfo.last_seen,
            });
          }
        }
      }

      const response = {
        users,
        total_count: users.length,
      };

      console.log(
        `✅ [UserService] Found ${users.length} online users in room ${room_id}`,
      );
      callback(null, response);
    } catch (error) {
      console.error(`❌ [UserService] Erro ao obter usuários online:`, error);

      const errorResponse = {
        users: [],
        total_count: 0,
      };

      callback(null, errorResponse);
    }
  }

  /**
   * Atualizar status do usuário
   * @param {Object} call - Objeto da chamada gRPC
   * @param {Function} callback - Callback para retornar a resposta
   */
  updateUserStatus(call, callback) {
    const request = call.request;
    const { user_id, status } = request;

    console.log(`🔄 [UserService] Updating user status:`);
    console.log(`   User ID: ${user_id}`);
    console.log(`   Status: ${status}`);

    try {
      if (!this.users.has(user_id)) {
        const errorResponse = {
          success: false,
          message: `Usuário ${user_id} não encontrado`,
        };
        callback(null, errorResponse);
        return;
      }

      const userInfo = this.users.get(user_id);
      userInfo.status = status;
      userInfo.last_seen = Date.now();

      // Se o usuário está saindo offline, remover das listas
      if (status === "OFFLINE") {
        const room_id = userInfo.room_id;

        if (this.onlineUsers.has(room_id)) {
          this.onlineUsers.get(room_id).delete(user_id);
        }

        if (this.usernameCache.has(room_id)) {
          this.usernameCache.get(room_id).delete(userInfo.username);
        }

        console.log(`👋 [UserService] User ${userInfo.username} went offline`);
      }

      const response = {
        success: true,
        message: `Status atualizado para ${status}`,
      };

      console.log(
        `✅ [UserService] Status updated for ${userInfo.username}: ${status}`,
      );
      callback(null, response);
    } catch (error) {
      console.error(`❌ [UserService] Erro ao atualizar status:`, error);

      const errorResponse = {
        success: false,
        message: `Erro interno: ${error.message}`,
      };

      callback(null, errorResponse);
    }
  }

  /**
   * Método para limpeza periódica de usuários inativos
   */
  cleanupInactiveUsers() {
    const now = Date.now();
    const inactiveThreshold = 30 * 60 * 1000; // 30 minutos

    for (const [user_id, userInfo] of this.users.entries()) {
      if (now - userInfo.last_seen > inactiveThreshold) {
        console.log(
          `🧹 [UserService] Cleaning up inactive user: ${userInfo.username}`,
        );

        const room_id = userInfo.room_id;

        // Remover das listas
        if (this.onlineUsers.has(room_id)) {
          this.onlineUsers.get(room_id).delete(user_id);
        }

        if (this.usernameCache.has(room_id)) {
          this.usernameCache.get(room_id).delete(userInfo.username);
        }

        this.users.delete(user_id);
      }
    }
  }

  /**
   * Iniciar limpeza automática de usuários inativos
   */
  startCleanupInterval() {
    setInterval(() => {
      this.cleanupInactiveUsers();
    }, 5 * 60 * 1000); // A cada 5 minutos
  }
}

/**
 * Função para iniciar o servidor gRPC
 */
function startServer() {
  const server = new grpc.Server();

  // Registra o serviço A
  const servicoAImpl = new ServicoAImpl();
  server.addService(servicoProto.ServicoA.service, {
    realizarTarefaA: servicoAImpl.realizarTarefaA.bind(servicoAImpl),
  });

  // Registra o serviço de usuários
  const userServiceImpl = new UserServiceImpl();
  server.addService(servicoProto.UserService.service, {
    loginUser: userServiceImpl.loginUser.bind(userServiceImpl),
    getOnlineUsers: userServiceImpl.getOnlineUsers.bind(userServiceImpl),
    updateUserStatus: userServiceImpl.updateUserStatus.bind(userServiceImpl),
  });

  // Inicia limpeza automática de usuários inativos
  userServiceImpl.startCleanupInterval();

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
      console.log("🔧 Serviços disponíveis:");
      console.log("   - ServicoA.RealizarTarefaA (método unary)");
      console.log("   - UserService.LoginUser (método unary)");
      console.log("   - UserService.GetOnlineUsers (método unary)");
      console.log("   - UserService.UpdateUserStatus (método unary)");
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
