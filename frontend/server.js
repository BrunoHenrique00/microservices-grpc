const express = require("express");
const cors = require("cors");
const axios = require("axios");
const { exec, spawn } = require("child_process");
const path = require("path");

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Servidores REST dos módulos A e B
let restServerA = null;
let restServerB = null;

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
    const response = await axios.post(
      "http://localhost:8000/api/executar",
      req.body
    );
    res.json({ success: true, data: response.data });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Proxy para módulo A REST
app.post("/api/test/modulo-a", async (req, res) => {
  try {
    const response = await axios.post(
      "http://localhost:5001/realizar-tarefa-a",
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
      "http://localhost:5002/realizar-tarefa-b",
      req.body
    );
    res.json({ success: true, data: response.data });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`🚀 Frontend: http://localhost:${PORT}`);

  // Iniciar servidores REST automaticamente
  startRestServers();
});
