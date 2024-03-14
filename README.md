# Querido Diário - Processamento de Dados

Este repositório contém todo o código do pipeline de processamento usado pelo
projeto Querido Diário para analisar os diários extraídos pelos raspadores.

Aqui, você encontrará os códigos usados no pipeline, juntamente com o Helm
chart usado para instalá-lo em um cluster Kubernetes.

## Como contribuir 

Para informações sobre contribuições e de como rodar o pipeline, leia o
CONTRIBUTING.md. Mas se você já tem instalado na máquina o minikube e o tilt,
execute:

```console
$ make cluster
$ tilt up --stream
```

