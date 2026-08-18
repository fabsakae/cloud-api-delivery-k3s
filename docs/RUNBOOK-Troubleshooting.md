# Runbook de Troubleshooting: Tokage API (K3s)

Este documento define os procedimentos de diagnóstico e mitigação para incidentes críticos na `tokage-api-delivery`.

## 1. Incidente: Falha de Memória (OOMKilled)
**Sintoma:** O pod da API reinicia frequentemente com status `OOMKilled` no `kubectl get pods`.
**Diagnóstico:** 
1. Acesse o Grafana (Porta 8081).
2. Verifique o dashboard "Tokage API". Se a curva de memória tocar o limite do *LimitRange* ou *ResourceQuota*, o pod será derrubado pelo K8s.

**Procedimento de Mitigação (Contorno):**
1. Escale as réplicas temporariamente para diluir a carga de memória:
   ```bash
   kubectl scale deployment tokage-api-delivery --replicas=4
   ```
2. Analise o consumo por réplica no Grafana. Se o vazamento persistir, verifique logs de erros:
    ```bash
    kubectl logs -l app=tokage-api-delivery --previous
    ```
## 2. Incidente: Falha na Conexão com DBaaS (PostgreSQL)
**Sintoma:** API retorna 500 Internal Server Error e logs indicam connection refused.
**Diagnóstico:** Verifique se o IP privado do banco mudou ou se o Security Group bloqueou o tráfego na porta 5432.

1. Teste a conectividade a partir de um pod de diagnóstico:
    ```bash
    kubectl run debug-db --rm -it --image=postgres -- psql -h <IP_PRIVADO_DB> -U <USER> -d orders
    ```

## 3. Incidente: Cluster Inacessível via Ingress

**Sintoma:** Erro 503 Service Unavailable ou Connection Refused ao acessar via browser.
**Diagnóstico:** 
1. Verifique o status do Traefik Ingress:
    ```bash
    kubectl get pods -n kube-system -l app.kubernetes.io/name=traefik
    ```
2. Verifique se as regras do Security Group na MGC para a porta 80 ou 8081 foram removidas ou alteradas.

## 4. Procedimento de Rollback (Emergência)

Se um deploy causar falha sistêmica, reverta para a última versão estável:
    ```bash
    kubectl rollout undo deployment/tokage-api-delivery
    ```
    
