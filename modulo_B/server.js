/**
 * Módulo B - Servidor gRPC em Node.js
 * Responsável por:
 * - Upload de arquivos via client-streaming
 * - Distribuição de arquivos para todos os usuários via bidirectional-streaming
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
 * Implementação do FileService
 * Gerencia upload de arquivos e distribuição para todos os usuários
 */
class FileServiceImpl {
  constructor() {
    // Armazenamento em memória dos arquivos {file_id: file_info}
    this.files = new Map();
    // Streams ativos de distribuição {room_id: Map(user_id -> call)}
    this.distributionStreams = new Map();
    // Limite de tamanho de arquivo: 25MB
    this.maxFileSize = 25 * 1024 * 1024;
    // Limite de chunk: 1MB
    this.maxChunkSize = 1 * 1024 * 1024;
  }

  /**
   * Upload de arquivo via client-streaming
   * Recebe múltiplos chunks e armazena o arquivo completo
   */
  uploadFile(call, callback) {
    const uploadSession = {
      chunks: [],
      metadata: {},
      totalSize: 0,
      receivedChunks: 0,
      expectedChunks: 0,
    };

    console.log(`📤 [FileService] Iniciando upload de arquivo...`);

    call.on("data", (chunk) => {
      try {
        // Primeira chunk contém metadata
        if (uploadSession.receivedChunks === 0) {
          uploadSession.metadata = {
            file_id: chunk.file_id,
            filename: chunk.filename,
            mime_type: chunk.mime_type,
            user_id: chunk.user_id,
            username: chunk.username,
            room_id: chunk.room_id,
            file_size: chunk.file_size,
          };
          uploadSession.expectedChunks = chunk.total_chunks;

          console.log(`📁 [FileService] Arquivo recebido:`);
          console.log(`   ID: ${chunk.file_id}`);
          console.log(`   Nome: ${chunk.filename}`);
          console.log(`   Usuário: ${chunk.username}`);
          console.log(
            `   Tamanho: ${(chunk.file_size / 1024 / 1024).toFixed(2)}MB`,
          );
          console.log(`   Total de chunks: ${chunk.total_chunks}`);

          // Validar tamanho
          if (chunk.file_size > this.maxFileSize) {
            const error = new Error(
              `Arquivo excede o limite de ${(
                this.maxFileSize /
                1024 /
                1024
              ).toFixed(0)}MB`,
            );
            call.emit("error", {
              code: grpc.status.INVALID_ARGUMENT,
              details: error.message,
            });
            return;
          }
        }

        // Validar chunk
        if (chunk.chunk_data.length > this.maxChunkSize) {
          const error = new Error(
            `Chunk excede o limite de ${(
              this.maxChunkSize /
              1024 /
              1024
            ).toFixed(0)}MB`,
          );
          call.emit("error", {
            code: grpc.status.INVALID_ARGUMENT,
            details: error.message,
          });
          return;
        }

        // Armazenar chunk
        uploadSession.chunks.push({
          index: chunk.chunk_index,
          data: chunk.chunk_data,
        });

        uploadSession.totalSize += chunk.chunk_data.length;
        uploadSession.receivedChunks++;

        console.log(
          `📥 [FileService] Chunk ${chunk.chunk_index + 1}/${
            chunk.total_chunks
          } recebido ` +
            `(${(uploadSession.totalSize / 1024 / 1024).toFixed(2)}MB)`,
        );

        // Se todos os chunks foram recebidos
        if (uploadSession.receivedChunks === uploadSession.expectedChunks) {
          this.finalizeUpload(uploadSession, callback);
        }
      } catch (error) {
        console.error(`❌ [FileService] Erro ao processar chunk:`, error);
        call.emit("error", {
          code: grpc.status.INTERNAL,
          details: error.message,
        });
      }
    });

    call.on("end", () => {
      // Se não recebeu todos os chunks
      if (
        uploadSession.receivedChunks > 0 &&
        uploadSession.receivedChunks < uploadSession.expectedChunks
      ) {
        console.warn(
          `⚠️ [FileService] Upload incompleto: ${uploadSession.receivedChunks}/${uploadSession.expectedChunks} chunks`,
        );
      }
    });

    call.on("error", (error) => {
      console.error(`❌ [FileService] Erro no stream de upload:`, error);
    });
  }

  /**
   * Finalizar upload e armazenar arquivo
   */
  finalizeUpload(uploadSession, callback) {
    try {
      const metadata = uploadSession.metadata;

      // Combinar todos os chunks em ordem
      const fileData = Buffer.concat(
        uploadSession.chunks
          .sort((a, b) => a.index - b.index)
          .map((c) => c.data),
      );

      // ================================
      // PROCESSAMENTO DO ARQUIVO
      // ================================

      // 1. Validação de integridade
      const calculatedSize = fileData.length;
      if (Math.abs(calculatedSize - metadata.file_size) > 1024) {
        // Tolerância de 1KB para diferenças
        console.warn(
          `⚠️  [FileService] Discrepância de tamanho: esperado ${metadata.file_size}, recebido ${calculatedSize}`,
        );
      }

      // 2. Detecção de tipo MIME (validação básica)
      const mimeType = this.detectMimeType(metadata.filename, fileData);
      console.log(`📋 [FileService] MIME Type detectado: ${mimeType}`);

      // 3. Calcular hash/checksum para integridade
      const crypto = require("crypto");
      const checksum = crypto
        .createHash("sha256")
        .update(fileData)
        .digest("hex");

      // 4. Validação de conteúdo (escanear vírus básico - simples para exemplo)
      const isSafe = this.validateFileContent(metadata.filename, fileData);
      if (!isSafe) {
        console.error(
          `🚨 [FileService] Arquivo possivelmente malicioso: ${metadata.filename}`,
        );
        const errorResponse = {
          success: false,
          file_id: metadata.file_id,
          filename: metadata.filename,
          file_size: 0,
          message: `Arquivo potencialmente malicioso rejeitado`,
          timestamp: Date.now(),
        };
        callback(null, errorResponse);
        return;
      }

      // Armazenar arquivo com metadados completos
      const fileInfo = {
        file_id: metadata.file_id,
        filename: metadata.filename,
        mime_type: mimeType,
        user_id: metadata.user_id,
        username: metadata.username,
        room_id: metadata.room_id,
        file_size: fileData.length,
        data: fileData,
        uploaded_at: Date.now(),
        checksum: checksum,
        is_safe: isSafe,
      };

      this.files.set(metadata.file_id, fileInfo);

      console.log(
        `✅ [FileService] Arquivo ${metadata.filename} salvo com sucesso`,
      );
      console.log(`   ID: ${metadata.file_id}`);
      console.log(
        `   Tamanho final: ${(fileData.length / 1024 / 1024).toFixed(2)}MB`,
      );
      console.log(`   Checksum SHA256: ${checksum}`);
      console.log(
        `   Status de segurança: ${isSafe ? "✅ Seguro" : "⚠️  Suspeito"}`,
      );

      // Notificar subscribers sobre o novo arquivo
      this.broadcastFileToRoom(metadata.room_id, fileInfo);

      // Retornar resposta de sucesso
      const response = {
        success: true,
        file_id: metadata.file_id,
        filename: metadata.filename,
        file_size: fileData.length,
        message: `Arquivo ${metadata.filename} enviado com sucesso`,
        timestamp: Date.now(),
        checksum: checksum,
      };

      callback(null, response);
    } catch (error) {
      console.error(`❌ [FileService] Erro ao finalizar upload:`, error);

      const errorResponse = {
        success: false,
        file_id: uploadSession.metadata.file_id || "",
        filename: uploadSession.metadata.filename || "",
        file_size: uploadSession.totalSize,
        message: `Erro ao salvar arquivo: ${error.message}`,
        timestamp: Date.now(),
      };

      callback(null, errorResponse);
    }
  }

  /**
   * Detectar tipo MIME do arquivo
   */
  detectMimeType(filename, fileData) {
    // Extensão do arquivo
    const ext = filename.split(".").pop()?.toLowerCase() || "";

    // Mapping simples de extensões
    const mimeTypes = {
      pdf: "application/pdf",
      txt: "text/plain",
      doc: "application/msword",
      docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      xls: "application/vnd.ms-excel",
      xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      jpg: "image/jpeg",
      jpeg: "image/jpeg",
      png: "image/png",
      gif: "image/gif",
      zip: "application/zip",
      mp4: "video/mp4",
      mp3: "audio/mpeg",
      mov: "video/quicktime",
    };

    // Verificar magic bytes (assinatura de arquivo)
    const magicBytes = this.getMagicBytes(fileData);
    if (magicBytes) {
      return magicBytes;
    }

    // Retornar MIME type por extensão ou genérico
    return mimeTypes[ext] || "application/octet-stream";
  }

  /**
   * Detectar tipo de arquivo por magic bytes
   */
  getMagicBytes(buffer) {
    if (buffer.length < 4) return null;

    // Verificar assinaturas conhecidas
    // PDF
    if (buffer[0] === 0x25 && buffer[1] === 0x50 && buffer[2] === 0x44) {
      return "application/pdf";
    }

    // PNG
    if (
      buffer[0] === 0x89 &&
      buffer[1] === 0x50 &&
      buffer[2] === 0x4e &&
      buffer[3] === 0x47
    ) {
      return "image/png";
    }

    // JPEG
    if (buffer[0] === 0xff && buffer[1] === 0xd8) {
      return "image/jpeg";
    }

    // ZIP / Office files
    if (buffer[0] === 0x50 && buffer[1] === 0x4b) {
      return "application/zip";
    }

    // GIF
    if (buffer[0] === 0x47 && buffer[1] === 0x49 && buffer[2] === 0x46) {
      return "image/gif";
    }

    return null;
  }

  /**
   * Validar segurança do arquivo
   */
  validateFileContent(filename, fileData) {
    // Verificações de segurança básicas

    // 1. Verificar se contém scripts perigosos (análise simples)
    const dangerousPatterns = [
      /eval\s*\(/gi, // JavaScript eval
      /script>/gi, // HTML script tags
      /onclick/gi, // Event handlers
    ];

    const fileStr = fileData.toString(
      "utf-8",
      0,
      Math.min(10000, fileData.length),
    );

    for (const pattern of dangerousPatterns) {
      if (pattern.test(fileStr)) {
        console.warn(
          `⚠️  [FileService] Padrão suspeito encontrado: ${pattern}`,
        );
        // Não rejeitar ainda, apenas alertar
      }
    }

    // 2. Verificar extensões perigosas
    const dangerousExtensions = [
      ".exe",
      ".bat",
      ".cmd",
      ".scr",
      ".com",
      ".pif",
      ".vbs",
    ];
    const ext = filename.substring(filename.lastIndexOf(".")).toLowerCase();
    if (dangerousExtensions.includes(ext)) {
      console.warn(
        `⚠️  [FileService] Extensão potencialmente perigosa: ${ext}`,
      );
    }

    // 3. Verificar tamanho
    if (fileData.length > 25 * 1024 * 1024) {
      console.error(
        `❌ [FileService] Arquivo muito grande: ${(
          fileData.length /
          1024 /
          1024
        ).toFixed(2)}MB`,
      );
      return false;
    }

    // Arquivo é considerado seguro se passou nas validações
    return true;
  }

  /**
   * Receber arquivos distribuídos via server-streaming
   */
  receiveFiles(call) {
    const request = call.request;
    const { room_id, file_id } = request;

    console.log(`📥 [FileService] Solicitação de arquivo:`);
    if (file_id) {
      console.log(`   File ID: ${file_id}`);
    } else {
      console.log(`   Room: ${room_id}`);
    }

    try {
      let files = [];

      // Se file_id específico é solicitado
      if (file_id && this.files.has(file_id)) {
        files = [this.files.get(file_id)];
      } else {
        // Caso contrário, retornar todos os arquivos da sala
        files = Array.from(this.files.values()).filter(
          (f) => f.room_id === room_id,
        );
      }

      console.log(`📤 [FileService] Enviando ${files.length} arquivo(s)`);

      let fileIndex = 0;

      // Enviar cada arquivo em chunks
      const sendNextFile = () => {
        if (fileIndex >= files.length) {
          call.end();
          return;
        }

        const file = files[fileIndex];
        const chunkSize = this.maxChunkSize;
        const totalChunks = Math.ceil(file.data.length / chunkSize);

        console.log(
          `📤 [FileService] Enviando arquivo ${fileIndex + 1}/${
            files.length
          }: ${file.filename}`,
        );

        let chunkIndex = 0;

        const sendNextChunk = () => {
          if (chunkIndex >= totalChunks || call.cancelled) {
            fileIndex++;
            sendNextFile();
            return;
          }

          const start = chunkIndex * chunkSize;
          const end = Math.min(start + chunkSize, file.data.length);
          const chunkData = file.data.slice(start, end);

          const fileChunk = {
            file_id: file.file_id,
            filename: file.filename,
            mime_type: file.mime_type,
            chunk_data: chunkData,
            chunk_index: chunkIndex,
            total_chunks: totalChunks,
            file_size: file.file_size,
            user_id: file.user_id,
            username: file.username,
            room_id: file.room_id,
          };

          call.write(fileChunk);
          chunkIndex++;

          // Enviar próximo chunk com pequeno delay
          setImmediate(sendNextChunk);
        };

        sendNextChunk();
      };

      sendNextFile();
    } catch (error) {
      console.error(`❌ [FileService] Erro ao enviar arquivos:`, error);
      call.emit("error", {
        code: grpc.status.INTERNAL,
        details: error.message,
      });
    }
  }

  /**
   * Distribuição de arquivo em tempo real via bidirectional-streaming
   */
  distributeFile(call) {
    let room_id = null;
    let user_id = null;
    let username = null;

    console.log(
      `🔄 [FileService] Nova conexão de distribuição de arquivo iniciada`,
    );

    call.on("data", (fileMessage) => {
      try {
        // Primeira mensagem contém informações da sessão
        if (!room_id) {
          room_id = fileMessage.room_id || "global";
          user_id = fileMessage.user_id;
          username = fileMessage.username;

          console.log(`✅ [FileService] Distribuidor conectado:`);
          console.log(`   Usuário: ${username}`);
          console.log(`   Sala: ${room_id}`);

          // Registrar stream do distribuidor
          if (!this.distributionStreams.has(room_id)) {
            this.distributionStreams.set(room_id, new Map());
          }
          this.distributionStreams.get(room_id).set(user_id, call);

          return;
        }

        // Receber e fazer broadcast do arquivo
        console.log(
          `📤 [FileService] Distribuindo arquivo: ${fileMessage.filename} ` +
            `(chunk ${fileMessage.chunk_index + 1}/${
              fileMessage.total_chunks
            })`,
        );

        // Broadcast para todos os usuários da sala (exceto o remetente)
        this.broadcastFileChunkToRoom(room_id, fileMessage, user_id);
      } catch (error) {
        console.error(`❌ [FileService] Erro ao distribuir arquivo:`, error);
      }
    });

    call.on("end", () => {
      console.log(
        `👋 [FileService] Distribuidor ${username} (${user_id}) encerrou conexão`,
      );
      if (room_id && this.distributionStreams.has(room_id)) {
        this.distributionStreams.get(room_id).delete(user_id);
      }
      call.end();
    });

    call.on("error", (error) => {
      console.error(`❌ [FileService] Erro na conexão de distribuição:`, error);
      if (room_id && this.distributionStreams.has(room_id)) {
        this.distributionStreams.get(room_id).delete(user_id);
      }
    });

    call.on("cancelled", () => {
      console.log(`🚫 [FileService] Conexão de distribuição cancelada`);
      if (room_id && this.distributionStreams.has(room_id)) {
        this.distributionStreams.get(room_id).delete(user_id);
      }
    });
  }

  /**
   * Faz broadcast de arquivo para todos usuários da sala
   */
  broadcastFileToRoom(room_id, fileInfo) {
    if (!this.distributionStreams.has(room_id)) {
      return;
    }

    const roomDistributors = this.distributionStreams.get(room_id);
    const disconnectedUsers = [];

    console.log(
      `📡 [FileService] Fazendo broadcast de ${fileInfo.filename} para ${roomDistributors.size} usuários`,
    );

    for (const [user_id, call] of roomDistributors.entries()) {
      if (user_id === fileInfo.user_id) {
        // Não enviar de volta para o uploader
        continue;
      }

      try {
        if (!call.cancelled && !call.destroyed) {
          // Dividir em chunks para envio
          const chunkSize = this.maxChunkSize;
          const totalChunks = Math.ceil(fileInfo.data.length / chunkSize);

          for (let i = 0; i < totalChunks; i++) {
            const start = i * chunkSize;
            const end = Math.min(start + chunkSize, fileInfo.data.length);
            const chunkData = fileInfo.data.slice(start, end);

            const fileMessage = {
              file_id: fileInfo.file_id,
              filename: fileInfo.filename,
              mime_type: fileInfo.mime_type,
              user_id: fileInfo.user_id,
              username: fileInfo.username,
              chunk_data: chunkData,
              chunk_index: i,
              total_chunks: totalChunks,
              file_size: fileInfo.file_size,
              room_id,
              type:
                i === 0
                  ? "FILE_START"
                  : i === totalChunks - 1
                  ? "FILE_END"
                  : "FILE_CHUNK",
              timestamp: Date.now(),
            };

            call.write(fileMessage);
          }
        } else {
          disconnectedUsers.push(user_id);
        }
      } catch (error) {
        console.error(
          `❌ [FileService] Erro ao enviar para usuário ${user_id}:`,
          error,
        );
        disconnectedUsers.push(user_id);
      }
    }

    // Limpar conexões mortas
    disconnectedUsers.forEach((user_id) => {
      roomDistributors.delete(user_id);
    });
  }

  /**
   * Faz broadcast de chunk de arquivo para todos usuários da sala
   */
  broadcastFileChunkToRoom(room_id, fileMessage, senderUserId) {
    if (!this.distributionStreams.has(room_id)) {
      return;
    }

    const roomDistributors = this.distributionStreams.get(room_id);
    const disconnectedUsers = [];

    for (const [user_id, call] of roomDistributors.entries()) {
      if (user_id === senderUserId) {
        // Não enviar de volta para o remetente
        continue;
      }

      try {
        if (!call.cancelled && !call.destroyed) {
          call.write(fileMessage);
        } else {
          disconnectedUsers.push(user_id);
        }
      } catch (error) {
        console.error(
          `❌ [FileService] Erro ao fazer broadcast do chunk:`,
          error,
        );
        disconnectedUsers.push(user_id);
      }
    }

    // Limpar conexões mortas
    disconnectedUsers.forEach((user_id) => {
      roomDistributors.delete(user_id);
    });
  }

  /**
   * Obter informações de arquivo
   */
  getFileInfo(file_id) {
    return this.files.get(file_id);
  }

  /**
   * Listar arquivos de uma sala
   */
  listFilesInRoom(room_id) {
    return Array.from(this.files.values())
      .filter((f) => f.room_id === room_id)
      .map((f) => ({
        file_id: f.file_id,
        filename: f.filename,
        mime_type: f.mime_type,
        file_size: f.file_size,
        user_id: f.user_id,
        username: f.username,
        uploaded_at: f.uploaded_at,
      }));
  }

  /**
   * Obter estatísticas do serviço
   */
  getStats() {
    const roomStats = {};

    for (const [room_id, distributors] of this.distributionStreams.entries()) {
      roomStats[room_id] = {
        active_distributors: distributors.size,
        total_files: this.listFilesInRoom(room_id).length,
      };
    }

    return {
      total_files: this.files.size,
      total_size: Array.from(this.files.values()).reduce(
        (sum, f) => sum + f.file_size,
        0,
      ),
      rooms: roomStats,
    };
  }
}

/**
 * Função para iniciar o servidor gRPC
 */
function startServer() {
  const server = new grpc.Server();

  // Registra o serviço de arquivos
  const fileServiceImpl = new FileServiceImpl();
  server.addService(servicoProto.FileService.service, {
    uploadFile: fileServiceImpl.uploadFile.bind(fileServiceImpl),
    receiveFiles: fileServiceImpl.receiveFiles.bind(fileServiceImpl),
    distributeFile: fileServiceImpl.distributeFile.bind(fileServiceImpl),
  });

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

      console.log("🚀 Servidor gRPC do Módulo B iniciado!");
      console.log(`📍 Endereço: ${serverAddress}`);
      console.log("🔧 Serviços disponíveis:");
      console.log("   - FileService.UploadFile (client-streaming)");
      console.log("   - FileService.ReceiveFiles (server-streaming)");
      console.log("   - FileService.DistributeFile (bidirectional-streaming)");
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
  console.log("🔧 Inicializando Módulo B (FileService)...");
  startServer();
}

module.exports = { FileServiceImpl, startServer };
