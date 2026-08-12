# ADR 0002: Estratégia de Ingress e ClusterIP no K3s

## Status
Aceito

## Contexto
No ambiente Kubernetes leve (K3s em nó único), o *Traefik* já vem instalado por padrão como o *Ingress Controller* nativo, ocupando a porta TCP 80 do nó hospedeiro (a VM na Magalu Cloud). 

Se tentar expor a API criando um Service do Kubernetes do tipo `LoadBalancer` na porta 80, o componente interno do K3s (ServiceLB) tentará reservar a mesma porta diretamente no nó. Isso causará um conflito de rede imediato, resultando no erro clássico `node(s) didn't have free ports for the requested pod ports` e deixando o serviço preso no status `<pending>`.

## Decisão
Decidi não utilizar um Service do tipo `LoadBalancer`. A nossa API será exposta usando a combinação de um Service **`ClusterIP`** interno com o **`Traefik Ingress`**.

## Justificativa
*   A aplicação vai rodar na porta 8000 dentro do container. O Service `ClusterIP` exporá a porta 80 apenas *internamente* no cluster, apontando para a porta 8000 do container. O recurso `Ingress` dirá ao Traefik: "Todo tráfego externo que chegar na VM deve ser roteado para o ClusterIP da API".
*   Isso resolve o conflito de portas na VM, pois o Traefik continuará sendo o único dono da porta 80 no hospedeiro.
*   Essa abordagem reflete as melhores práticas do mercado corporativo. Em vez de dar um IP público (LoadBalancer) para cada microsserviço que a empresa cria, usamos um único Ingress Controller (como um porteiro do prédio) para receber todo o tráfego externo e roteá-lo internamente para os serviços corretos.

## Consequências
1.  Para que a aplicação seja testada externamente pelo navegador ou via `curl`, a porta TCP 80 precisará ser liberada no Security Group da VM na Magalu Cloud.