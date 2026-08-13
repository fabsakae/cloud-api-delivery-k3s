# Cloud API Delivery & K3s (DevSecOps Pipeline)

Este repositório contém a infraestrutura como código (IaC) e a esteira de automação (CI/CD) para o provisionamento, segurança e entrega contínua de uma API REST em um cluster Kubernetes, utilizando os serviços da Magalu Cloud.

##  Objetivos de Negócio e Engenharia

Este projeto foi desenhado para resolver três desafios críticos na operação de engenharia de software:

*   **Remoção de Gargalos na Entrega (CI/CD):** Substituição de deploys manuais por uma esteira automatizada no GitHub Actions, garantindo que o código seja empacotado, testado e publicado de forma padronizada, rápida e auditável.
*   **Segurança Contínua (Shift-Left Security):** Integração de análises estáticas de segurança (SAST) com CodeQL e verificação de composição de software (SCA) com Dependabot. A esteira bloqueia proativamente vulnerabilidades críticas antes que cheguem ao ambiente de produção.
*   **Alta Disponibilidade e Self-Healing:** Arquitetura resiliente baseada em Kubernetes (K3s). A aplicação opera no modelo *stateless*, com o estado isolado em um banco de dados gerenciado (DBaaS PostgreSQL). Em caso de falhas de memória (OOMKilled) ou travamentos, o cluster orquestra a auto-recuperação sem indisponibilidade para o usuário final.

---

##  Diagrama de Arquitetura (C4 Model - Nível 2)

A topologia da solução reflete um fluxo seguro e automatizado, desde o commit da desenvolvedora até a exposição segura da aplicação:

```mermaid
flowchart TD
    dev([" Desenvolvedora"])

    subgraph GitHub ["GitHub"]
        repo[/" Repositório Git"/]
        actions[[" GitHub Actions (CI/CD)"]]
    end

    subgraph MGC ["Magalu Cloud (MGC)"]
        registry[/" MGC Container Registry"/]
        dbaas[(" PostgreSQL DBaaS (BV1-4-10)")]
        
        subgraph K8s ["Cluster Kubernetes (K3s)"]
            ingress{" Traefik Ingress"}
            api[" App API REST (2 Réplicas)"]
            prometheus[" Prometheus & Grafana"]
        end
    end

    %% Relacionamentos
    dev -- "1. Git Push" --> repo
    repo -- "2. Dispara Workflow" --> actions
    actions -- "3. Push Imagem Docker" --> registry
    actions -- "4. Aplica Manifestos (kubectl)" --> K8s
    
    ingress -- "5. Roteia tráfego TCP 80" --> api
    api -- "6. Lê/Grava Dados (TCP 5432)" --> dbaas
    prometheus -- "7. Scrape (/metrics)" --> api
    K8s -- "8. Pull Imagem" --> registry
```

---

##  Stack Tecnológica

*   **Orquestração e Containers:** Kubernetes (K3s), Docker.
*   **Automação e CI/CD:** GitHub Actions.
*   **Segurança (DevSecOps):** CodeQL (SAST), Dependabot (SCA), Kubernetes Secrets.
*   **Provedor Cloud (MGC):** Magalu Cloud (CLI, Container Registry, DBaaS PostgreSQL, VM/Security Groups).
*   **Observabilidade:** Prometheus, Grafana.

---

##  Documentação e Decisões Arquiteturais (ADRs)

Para garantir a rastreabilidade e facilitar a resposta a incidentes, as decisões de engenharia e os procedimentos operacionais estão documentados na pasta `docs/`:

*   **[ADR-0001: Adoção de Banco de Dados Externo (DBaaS)](docs/ADR-0001-DBaaS.md)**
*   **[ADR-0002: Estratégia de Ingress e ClusterIP no K3s](docs/ADR-0002-Ingress-ClusterIP.md)**
*   **[Runbook: Troubleshooting de Falhas no Kubernetes](docs/RUNBOOK-Troubleshooting.md)**

##  CI/CD Pipeline (GitHub Actions)

A entrega contínua (Continuous Delivery) é orquestrada pelo arquivo `.github/workflows/deploy.yml`. 

**Gatilhos (Triggers):**
- `push` na branch `main`.
- Disparo manual via `workflow_dispatch`.

**Etapas da Esteira (Jobs):**
1. **Checkout:** Clona o código-fonte no *runner* isolado (Ubuntu-latest).
2. **Autenticação Segura:** Faz o login no Magalu Cloud Container Registry sem expor credenciais no log.
3. **Metadados e Tags:** Gera tags automáticas para a imagem baseadas no *commit* (rastreabilidade).
4. **Build & Push OCI:** Constrói a imagem Docker baseada no `Dockerfile` e a publica na nuvem com suporte a cache (`type=gha`) para otimizar o tempo de execução.

**Requisitos de Segurança (GitHub Secrets):**
Para que a esteira tenha permissão de gravar no repositório da nuvem, os seguintes *Secrets* devem ser obrigatoriamente configurados nas configurações do repositório:
- `MAGALU_REGISTRY_USERNAME`
- `MAGALU_REGISTRY_PASSWORD`

##  Como Executar o Projeto (Passo a Passo)

### 1. Provisionamento da Infraestrutura (Magalu Cloud)
Criação da Máquina Virtual via MGC CLI dimensionada para suportar a carga de trabalho:
```bash
mgc virtual-machines instances create \
  --name api-cluster-k3s \
  --image.name "cloud-ubuntu-24.04 LTS" \
  --machine-type.name BV2-4-40 \
  --network.associate-public-ip true \
  --ssh-key-name chave_api_k3s
```

### 2. Configuração do Orquestrador e CI/CD
- Instalação do motor Kubernetes (K3s) na máquina provisionada.
- Configuração dos `Secrets` de autenticação no repositório do GitHub (`MAGALU_REGISTRY_USERNAME` e `MAGALU_REGISTRY_PASSWORD`).
- Disparo automático da esteira no GitHub Actions (via `git push`) para a construção da imagem Docker e envio ao MGC Container Registry.


### 3. Implantação no Kubernetes (Manifestos Declarativos)
Com a VM rodando e a imagem construída, a aplicação da infraestrutura imutável é feita via `kubectl`:
```bash
# 1. Criação da fronteira lógica (Namespace)
kubectl apply -f namespace.yml

# 2. Configuração do Secret de pull para o Registry Privado
kubectl create secret docker-registry mgc-registry-secret \
  --namespace move-tech-api \
  --docker-server=container-registry.br-se1.magalu.cloud \
  --docker-username='SEU_USUARIO' \
  --docker-password='***'

# 3. Orquestração da API (Deployment com 2 réplicas e Self-Healing)
kubectl apply -f deployment.yml

# 4. Roteamento interno e balanceamento de carga (Service)
kubectl apply -f service.yml
```

### 4. Exposição Externa (Ingress e Roteamento)
Para permitir que a API seja acessada pela internet, configuramos o Ingress Controller nativo (Traefik) e ajustamos as regras de segurança (Firewall) no provedor em nuvem.

**Configuração do Traefik Ingress:**
Aplicação do manifesto de Ingress para mapear a porta 80 pública para o Service interno:
```bash
kubectl apply -f ingress.yml
```

**Liberação de Tráfego no Firewall (Magalu Cloud):**
Para evitar o descarte de pacotes (`Timeout`), foi adicionada uma regra de entrada (*Inbound Rule*) no Security Group da Máquina Virtual, permitindo o tráfego HTTP público:
- **Protocolo:** TCP
- **Porta:** 80
- **Origem (Source):** `0.0.0.0/0` (Qualquer IP)

**Validação Externa:**
Teste de saúde e roteamento apontando diretamente para o IP Público associado à VM:
```bash
curl http://<IP_PUBLICO_MGC>/health
```

### 5. Provisionamento do Banco de Dados e Segurança (Em Desenvolvimento)
- [ ] Criação do DBaaS PostgreSQL na Magalu Cloud.
- [ ] Conexão da API com o banco via Kubernetes Secrets.
- [ ] Implementação de ferramentas SAST (CodeQL) e SCA (Dependabot).