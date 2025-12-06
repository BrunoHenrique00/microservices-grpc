// Módulo A - Servidor REST/JSON em Node.js

const express = require("express");
const app = express();
app.use(express.json());

// Inicializa métricas Prometheus
const client = require("prom-client");

// Se quiser, também carrega métricas customizadas do arquivo metrics.js
try {
  require("./metrics");
} catch (e) {
  console.log("⚠️ Nenhum arquivo metrics.js encontrado ou falhou ao carregar.");
}

// Coleta métricas padrão do Node
client.collectDefaultMetrics({
  prefix: "modulo_a_",
  timeout: 5000,
});

// Exemplo de contador para saber quantas vezes o endpoint REST foi chamado
const restRequestCounter = new client.Counter({
  name: "modulo_a_rest_requests_total",
  help: "Total de requisições recebidas no endpoint REST /realizar-tarefa-a",
});

// Endpoint REST que simula a lógica do método gRPC RealizarTarefaA
app.post("/realizar-tarefa-a", (req, res) => {
  restRequestCounter.inc(); // incrementa métrica

  const { id, data, operation } = req.body;
  console.log(`[REST][A] Requisição recebida:`, { id, data, operation });

  let result;
  switch (operation) {
    case "upper":
      result = (data || "").toUpperCase();
      break;
    case "reverse":
      result = (data || "").split("").reverse().join("");
      break;
    default:
      result = data;
  }

  res.json({
    id,
    resultado: result,
    status: "ok",
  });
});

// ENDPOINT /metrics — requerido pelo Prometheus
app.get("/metrics", async (req, res) => {
  try {
    res.set("Content-Type", client.register.contentType);
    res.end(await client.register.metrics());
  } catch (err) {
    res.status(500).end(err);
  }
});

const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
  console.log(`🔥 Servidor REST do Módulo A rodando na porta ${PORT}`);
  console.log(`📊 Métricas disponíveis em http://localhost:${PORT}/metrics`);
});
