# Documentação Teórica: gRPC, Protobuf e HTTP/2

## O que é gRPC?
gRPC é um framework open source de comunicação remota desenvolvido pela Google, que facilita a criação de aplicações distribuídas e microserviços. Ele utiliza o protocolo HTTP/2 para transporte e Protocol Buffers (protobuf) para serialização de dados, proporcionando alta performance, baixo consumo de banda e suporte nativo a múltiplas linguagens.

## Componentes do gRPC

### 1. Protocol Buffers (protobuf)
- É uma linguagem de definição de interface (IDL) e um mecanismo eficiente de serialização de dados.
- Permite definir mensagens e serviços em arquivos `.proto`, que são usados para gerar código em diversas linguagens (Python, Node.js, Go, Java, etc).
- Exemplo de mensagem em protobuf:
  ```proto
  message Exemplo {
    string nome = 1;
    int32 idade = 2;
  }
  ```

### 2. HTTP/2
- Protocolo de transporte utilizado pelo gRPC.
- Permite multiplexação de streams (várias requisições/respostas simultâneas na mesma conexão), compressão de cabeçalhos e comunicação bidirecional eficiente.
- Garante menor latência e melhor uso de recursos em comparação ao HTTP/1.1.

### 3. Stubs e Serviços
- O servidor implementa os métodos definidos no arquivo `.proto`.
- O cliente utiliza um stub (código gerado) para chamar métodos remotos como se fossem funções locais.

## Tipos de Comunicação gRPC
O gRPC suporta quatro tipos principais de chamadas:

1. **Unary**: Cliente envia uma requisição e recebe uma resposta única.
2. **Server Streaming**: Cliente envia uma requisição e recebe um fluxo de respostas do servidor.
3. **Client Streaming**: Cliente envia um fluxo de requisições e recebe uma resposta única do servidor.
4. **Bidirectional Streaming**: Cliente e servidor trocam fluxos de mensagens simultaneamente.

### Exemplos de uso
- **Unary**: Consultas simples, como buscar dados por ID.
- **Server Streaming**: Download de arquivos em partes, envio de logs contínuos.
- **Client Streaming**: Upload de arquivos em partes, envio de lotes de dados.
- **Bidirectional Streaming**: Chat em tempo real, processamento de dados em pipeline.

## Vantagens do gRPC
- Performance superior ao REST/JSON devido à serialização binária e HTTP/2.
- Suporte a múltiplas linguagens.
- Contratos de interface bem definidos via arquivos `.proto`.
- Suporte nativo a streaming e comunicação bidirecional.

## Desvantagens do gRPC
- Menor legibilidade dos dados (binário ao invés de JSON).
- Integração mais complexa com navegadores (por conta do HTTP/2 e CORS).
- Curva de aprendizado inicial para definição de protos e geração de código.

## Conclusão sobre os tipos de comunicação
gRPC é ideal para aplicações que exigem alta performance, comunicação eficiente entre microserviços e suporte a streaming. Cada tipo de chamada atende a cenários específicos:
- Use **Unary** para operações simples e rápidas.
- Use **Streaming** quando houver necessidade de enviar ou receber grandes volumes de dados ou comunicação contínua.
- Use **Bidirectional Streaming** para cenários interativos e de troca constante de mensagens.

---

> Consulte os exemplos práticos e o arquivo `servico.proto` para ver como cada tipo de chamada é implementado na prática.
