# Cloud Native

O termo "Cloud Native" refere-se a um paradigma de desenvolvimento e execução de aplicações projetadas especificamente para ambientes de computação em nuvem. Essa abordagem vai além de simplesmente "rodar uma aplicação na nuvem"; ela busca aproveitar ao máximo os recursos de elasticidade, resiliência e automação que esses ambientes oferecem.

Aplicações cloud native são geralmente construídas como um conjunto de microsserviços, empacotadas em contêineres e orquestradas por plataformas como o Kubernetes. O objetivo final é construir sistemas que sejam escaláveis, robustos e que possam ser atualizados de forma rápida e segura, promovendo agilidade para o negócio.

## Os Pilares Fundamentais do Cloud Native

A abordagem Cloud Native se sustenta em alguns pilares fundamentais. Nosso projeto aplica diretamente três desses pilares:

### 1. Arquitetura de Microsserviços
Aplicações monolíticas tradicionais são substituídas por um conjunto de serviços pequenos, independentes e focados em uma única responsabilidade de negócio. Eles se comunicam através de APIs bem definidas (como gRPC ou REST).

### 2. Containerização
Cada microsserviço é empacotado com todas as suas dependências (bibliotecas, runtime, etc.) em uma unidade isolada e portátil chamada contêiner. A tecnologia mais popular para isso é o Docker. Isso resolve o clássico problema do "funciona na minha máquina", garantindo que a aplicação se comporte da mesma forma em qualquer ambiente.

### 3. Orquestração de Contêineres
Quando se tem múltiplos microsserviços em contêineres, é necessário uma ferramenta para gerenciar seu ciclo de vida: o orquestrador. O Kubernetes é o padrão de mercado para essa tarefa, automatizando o deploy, o escalonamento, a recuperação de falhas e a rede entre os contêineres.