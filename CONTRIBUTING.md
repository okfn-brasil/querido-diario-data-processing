## Contribuições

Atualmente, o pipeline é executado em um cluster Kubernetes e é composto por
vários componentes que precisam estar acessíveis ao processo de processamento
dos diários. Esses componentes incluem:

- Elasticsearch: usado para indexar os textos.
- S3/Minio/Digital Ocean Spaces: armazenamento utilizado para guardar os
  arquivos dos diários e possíveis arquivos gerados pelo pipeline. Este
  armazenamento pode ser qualquer aplicação que se comunique pelo protocolo S3.
- Apache Tika: serviço que transforma os arquivos dos diários oficiais em
  arquivos de texto puro.
- PostgreSQL: base de dados utilizada para armazenar os metadados dos diários
  obtidos pelos raspadores.

**Importante:** Devido à diversidade de componentes, é necessário destacar que
uma quantidade considerável de recursos computacionais da máquina é necessária
para executar tudo localmente.

Lembrando que, como todos os componentes rodam dentro de um cluster Kubernetes,
ao acessar manualmente algum serviço, será necessário expor o serviço para fora
do cluster ou executar comandos dentro do cluster.

### Executando o Pipeline Localmente

Para executar o pipeline a partir do código disponível no repositório, são
necessários alguns pré-requisitos:

- Um cluster Kubernetes (recomendado o
  [Minikube](https://minikube.sigs.k8s.io/docs/)).
- [Kubectl](https://kubernetes.io/pt-br/docs/tasks/tools/#kubectl) para gerenciar o cluster.
- [Podman](https://podman.io/getting-started/installation): utilizado para
  criar os containers.
- [s3cmd](https://github.com/s3tools/s3cmd): comando utilizado apenas para preparar o ambiente de teste. Este programa é utilizado para copiar alguns arquivos de diário para o ambiente de
  teste.
- [PostgreSQL 12](https://www.postgresql.org/download/) também para preparar o ambiente de teste. Este programa é utilizado para popular o banco de dados relacional.

Para criar um cluster no Minikube com todos os componentes necessários
instalados, execute o seguinte comando:

```console
make setup
```

Após o cluster estar em execução, vamos preparar um ambiente com alguns dados
para serem processados pelo pipeline com o seguinte comando:

```console
make prepara-ambiente
```

Esse comando baixará e armazenará 5 diários, criará a base de dados no
PostgreSQL e marcará esses mesmos 5 diários como pendentes para serem
processados.

Antes de instalar o pipeline propriamente dito, crie as imagens dos containers
utilizados e carregue-as no cluster do Minikube. Caso contrário, o pipeline
baixará essas imagens do registro oficial do projeto do Querido Diário:

```console
make build-pipeline-image carrega-images
```

Depois que tudo estiver instalado no cluster, instale o pipeline:

```console
make install-pipeline
```

Em resumo, para executar o pipeline localmente sem alterações, execute:

```console
make setup prepara-ambiente build-pipeline-image carrega-images install-pipeline
```

Em seguida, você pode usar o `kubectl` ou `minikube kubectl` para acessar o
pipeline e seus componentes em execução no Kubernetes.

### Comandos Úteis

Nesta seção, estão descritos alguns comandos úteis para auxiliar no
desenvolvimento.

#### Credenciais dos Serviços Instalados

Tanto o PostgreSQL quanto o Elasticsearch precisam de credenciais para acesso.
Essas credenciais podem ser listadas com:

```console
make credenciais
```

#### Expor Serviços do Cluster para a Máquina Local

Para expor os serviços do MinIO e PostgreSQL e ter acesso fora do cluster, pode
ser utilizado o comando:

```console
make expoe-servicos
```

Esse comando colocará em execução em segundo plano alguns comandos `kubectl
port-forward`, mapeando os serviços do cluster Kubernetes para uma porta local.

Para remover esse mapeamento, execute:

```console
make derruba-servicos
```

#### Acessar a Base de Dados no Cluster

Se for necessário acessar o shell de acesso do PostgreSQL para executar algum
comando SQL, execute o seguinte comando:

```console
make shell-database
```

#### Executar Comandos no Elasticsearch

Como o Elasticsearch está rodando dentro do cluster, para enviar requisições
para o serviço, é necessário executar o comando `curl` de um container dentro
do cluster:

```console
kubectl run curl --rm -ti --restart="Never" --image curlimages/curl:8.4.0 -- -u elastic:<senha> "http://querido-diario-elasticsearch-es-http.default.svc.cluster.local:9200/querido-diario"
```

Observe que a `<senha>` pode ser obtida com o comando `make credenciais`.

