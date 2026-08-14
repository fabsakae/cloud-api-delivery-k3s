# ADR 0001: Adoção de Banco de Dados Externo (DBaaS)

## Status
Aceito

## Contexto
O projeto `cloud-api-delivery-k3s` requer um banco de dados relacional para persistência dos dados da API REST. Em arquiteturas baseadas em Kubernetes, existe o dilema de hospedar o banco de dados dentro do próprio cluster (como StatefulSets) ou delegar essa responsabilidade para um serviço gerenciado externo. 

Hospedar bancos de dados dentro de um cluster K3s de nó único (Single-Node) aumenta o risco de indisponibilidade geral em casos de pico de consumo de memória (OOMKilled), além de tornar o processo de backup e restauração consideravelmente mais complexo.

## Decisão
Decidi utilizar o **PostgreSQL na modalidade DBaaS (Database as a Service)** provido pela Magalu Cloud, utilizando uma instância dedicada do tipo `BV2-4-40` (2 vCPU, 4 GB RAM, 40 GiB Storage). 

## Justificativa
*   A conexão da API com o banco será feita estritamente via rede, utilizando variáveis de ambiente injetadas nos pods através de `Kubernetes Secrets` e `GitHub Secrets` (para a pipeline).
*   Isso remove completamente a camada de estado (*state*) de dentro do cluster Kubernetes.
*   Permite que os pods da API se tornem componentes puramente *stateless* (sem estado). Dessa forma, se a aplicação travar ou o cluster precisar ser recriado, os dados estarão seguros e isolados na infraestrutura gerenciada do provedor, facilitando o *Self-Healing* (auto-recuperação) do Kubernetes.

## Consequências
1.  **Segurança:** A string de conexão (`DATABASE_URL`) deverá ser rigorosamente protegida e não poderá, sob nenhuma hipótese, ser comitada em texto plano.
2.  **Rede:** Será necessário configurar as regras de acesso (Security Groups) do banco de dados na Magalu Cloud para aceitar conexões vindas exclusivamente do IP da VM do nosso cluster K3s.