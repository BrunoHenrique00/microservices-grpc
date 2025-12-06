// Módulo B - Servidor REST/JSON em Node.js
// Exemplo simples usando Express

const express = require("express");
const client = require("prom-client");

const app = express();
app.use(express.json());

// MÉTRICAS PROMETHEUS

// Coletar métricas padrão do Node.js (CPU, Memória, etc.)
const collectDefaultMetrics = client.collectDefaultMetrics;
collectDefaultMetrics();

// Rota para o Prometheus ler as métricas
app.get("/metrics", async (req, res) => {
  try {
    res.set("Content-Type", client.register.contentType);
    res.end(await client.register.metrics());
  } catch (ex) {
    res.status(500).end(ex);
  }
});

// Health check endpoint
app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok", service: "modulo-b-rest" });
});

// Endpoint REST que simula a lógica do método gRPC RealizarTarefaB (server-streaming)
app.post("/realizar-tarefa-b", (req, res) => {
  const { id, data, count } = req.body;
  console.log(`[REST][B] Requisição recebida:`, { id, data, count });

  // Simula múltiplas respostas (como streaming)
  const responseCount = Math.min(Math.max(count || 3, 1), 10);
  const resultados = [];
  for (let i = 1; i <= responseCount; i++) {
    resultados.push({
      id,
      resultado: `${data}-resp${i}`,
      ordem: i,
      status: "ok",
    });
  }

  res.json({
    id,
    respostas: resultados,
    total: responseCount,
  });
});

const PORT = process.env.PORT || 5002;
app.listen(PORT, () => {
  console.log(`Servidor REST do Módulo B rodando na porta ${PORT}`);
});
