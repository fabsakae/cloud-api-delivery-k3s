#!/bin/bash
# Automação de Provisionamento - Node K3s
set -e

echo "Solicitando a criação da Máquina Virtual na Magalu Cloud..."

mgc virtual-machines instances create \
  --name api-cluster-k3s \
  --image.name "cloud-ubuntu-24.04 LTS" \
  --machine-type.name BV2-4-40 \
  --network.associate-public-ip true \
  --ssh-key-name chave_api_k3s

echo "Ordem de provisionamento enviada com sucesso!"