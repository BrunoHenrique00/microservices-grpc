// Módulo A - Servidor REST/JSON em Node.js
// Exemplo simples usando Express

const express = require("express");
const app = express();
app.use(express.json());

// Endpoint REST que simula a lógica do método gRPC RealizarTarefaA
app.post("/realizar-tarefa-a", (req, res) => {
  const { id, data, operation } = req.body;
  console.log(`[REST][A] Requisição recebida:`, { id, data, operation });

  // Simula processamento
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

const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
  console.log(`Servidor REST do Módulo A rodando na porta ${PORT}`);
});
