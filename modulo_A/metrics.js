const express = require("express");
const client = require("prom-client");

const app = express();
const register = new client.Registry();

// Coleta métricas padrões do Node
client.collectDefaultMetrics({ register });

app.get("/metrics", async (req, res) => {
  res.setHeader("Content-Type", register.contentType);
  res.send(await register.metrics());
});

const PORT = 5001;

app.listen(PORT, () => {
  console.log(`[Métricas] Servidor HTTP de métricas rodando em :${PORT}`);
});
