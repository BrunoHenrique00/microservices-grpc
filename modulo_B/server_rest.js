// Módulo B - Servidor REST/JSON em Node.js
// Exemplo simples usando Express

const express = require("express");
const app = express();
app.use(express.json());

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
