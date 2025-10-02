# Arquitetura do Kubernetes

O Kubernetes é uma plataforma open source para orquestração de contêineres, responsável por automatizar o deploy, o gerenciamento, a escalabilidade e a recuperação de aplicações containerizadas. Seus principais componentes são:

- **Pod:** Unidade básica de deploy, que pode conter um ou mais contêineres.
- **Service:** Abstração que expõe pods para comunicação interna ou externa.
- **Deployment:** Gerencia o ciclo de vida dos pods, garantindo alta disponibilidade e atualizações sem downtime.
- **ConfigMap/Secret:** Permitem gerenciar configurações e dados sensíveis separadamente do código.
- **Ingress:** Controla o acesso externo aos serviços do cluster.

O Kubernetes facilita o deploy de aplicações distribuídas, garantindo escalabilidade, tolerância a falhas e automação de tarefas operacionais.
