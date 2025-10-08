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

// Página principal
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "index.html"));
});

// Proxy para teste principal
app.post("/api/test/executar", async (req, res) => {
  try {
    const response = await axios.post(
      "http://modulo-p:8000/api/executar",
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

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`🚀 Frontend: http://localhost:${PORT}`);
});
