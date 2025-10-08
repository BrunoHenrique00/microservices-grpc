const express = require("express");
const cors = require("cors");
const axios = require("axios");
const path = require("path");
const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(express.json());
// Servir arquivos estáticos (CSS, imagens, etc)
app.use(express.static(__dirname));

// Servidores REST dos módulos A e B
let restServerA = null;
let restServerB = null;

const GATEWAY_URL = process.env.GATEWAY_URL || "http://modulo-p:8000";

// Função para iniciar servidores REST
function startRestServers() {
  const projectDir = path.join(__dirname, "..");

  // Módulo A REST (porta 5001)
  if (!restServerA) {
    restServerA = spawn("node", ["server_rest.js"], {
      cwd: path.join(projectDir, "modulo_A"),
      env: { ...process.env, PORT: "5001" },
    });
    console.log("🟢 Módulo A REST rodando na porta 5001");
  }

  // Módulo B REST (porta 5002)
  if (!restServerB) {
    restServerB = spawn("node", ["server_rest.js"], {
      cwd: path.join(projectDir, "modulo_B"),
      env: { ...process.env, PORT: "5002" },
    });
    console.log("🟢 Módulo B REST rodando na porta 5002");
  }
}

// Página principal
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "index.html"));
});

// Proxy para teste principal
app.post("/api/test/executar", async (req, res) => {
  try {
    const response = await axios.post(`${GATEWAY_URL}/api/executar`, req.body);
    res.json({ success: true, data: response.data });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Proxy para módulo A REST
app.post("/api/test/modulo-a", async (req, res) => {
  try {
    const response = await axios.post(
      "http://modulo-a:5001/realizar-tarefa-a",
      req.body
    );
    res.json({ success: true, data: response.data });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Proxy para módulo B REST
app.post("/api/test/modulo-b", async (req, res) => {
  try {
    const response = await axios.post(
      "http://modulo-b:5002/realizar-tarefa-b",
      req.body
    );
    res.json({ success: true, data: response.data });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Endpoint para comparar tempos de resposta gRPC (via gateway) e REST (direto)
app.post("/api/test/comparar", async (req, res) => {
  const { id, data, operation, count } = req.body;
  // Realiza 5 requisições de cada tipo para obter média
  const N = 5;
  let grpcTimes = [],
    restTimes = [],
    grpcError = null,
    restError = null,
    grpcResult = null,
    restResult = null;
  for (let i = 0; i < N; i++) {
    try {
      const grpcStart = Date.now();
      const grpcResp = await axios.post(`${GATEWAY_URL}/api/executar`, {
        id,
        data,
        operation,
        count,
      });
      grpcTimes.push(Date.now() - grpcStart);
      if (i === 0) grpcResult = grpcResp.data;
    } catch (err) {
      grpcError = err.message;
      grpcTimes.push(null);
    }
    try {
      const restStart = Date.now();
      const restResp = await axios.post(
        "http://modulo-a:5001/realizar-tarefa-a",
        { id, data, operation }
      );
      restTimes.push(Date.now() - restStart);
      if (i === 0) restResult = restResp.data;
    } catch (err) {
      restError = err.message;
      restTimes.push(null);
    }
  }
  // Calcula médias (ignorando erros)
  const grpcValid = grpcTimes.filter((t) => t !== null);
  const restValid = restTimes.filter((t) => t !== null);
  const grpcAvg = grpcValid.length
    ? Math.round(grpcValid.reduce((a, b) => a + b, 0) / grpcValid.length)
    : null;
  const restAvg = restValid.length
    ? Math.round(restValid.reduce((a, b) => a + b, 0) / restValid.length)
    : null;
  res.json({
    grpc: {
      avg: grpcAvg,
      times: grpcTimes,
      result: grpcResult,
      error: grpcError,
    },
    rest: {
      avg: restAvg,
      times: restTimes,
      result: restResult,
      error: restError,
    },
    diff: grpcAvg !== null && restAvg !== null ? grpcAvg - restAvg : null,
    n: N,
  });
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`🚀 Frontend: http://localhost:${PORT}`);
});
