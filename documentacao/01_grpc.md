# gRPC: Componentes, Protocol Buffers e HTTP/2

gRPC é um framework moderno de comunicação remota desenvolvido pela Google, que facilita a criação de sistemas distribuídos de alta performance. Ele utiliza dois componentes principais:

- **Protocol Buffers (protobuf):** É uma linguagem de definição de interface (IDL) e um formato binário eficiente para serialização de dados. Permite definir mensagens e serviços em arquivos `.proto`, que são usados para gerar código em várias linguagens.
- **HTTP/2:** O gRPC utiliza o protocolo HTTP/2, que oferece multiplexação de streams, compressão de cabeçalhos e comunicação bidirecional eficiente, reduzindo latência e melhorando o desempenho em relação ao HTTP/1.1.

O gRPC suporta quatro tipos de chamadas: Unary, Server-streaming, Client-streaming e Bidirectional-streaming, tornando-o ideal para aplicações que exigem comunicação rápida e eficiente entre microsserviços.
