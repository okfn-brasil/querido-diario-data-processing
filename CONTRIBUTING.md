Bem-vindo ao guia de contribuição! Este documento foi preparado para fornecer
todas as informações necessárias para configurar e utilizar o ambiente de
desenvolvimento do nosso projeto de maneira eficiente. Primeiro, entenderemos
os componentes essenciais da nossa aplicação e, em seguida, detalharemos os
passos para preparar tudo.

## Componentes Necessários para a Aplicação

A nossa aplicação é composta por diversos componentes essenciais que trabalham
em conjunto para oferecer a melhor experiência possível:

- **MinIO**: Um armazenamento de objetos de alta performance, compatível com o
  protocolo Amazon S3. Usamos o MinIO para armazenar arquivos e dados
  necessários para a aplicação. [Saiba mais](https://min.io/).
- **OpenSearch**: O motor de busca que possibilita buscas textuais, análises e
  agregações de dados armazenados. É um componente chave para as
  funcionalidades de pesquisa da nossa aplicação. [Saiba
  mais](https://opensearch.org/).
- **Apache Tika**: Um toolkit para detecção e extração de conteúdo, que nos
  ajuda a extrair metadados e texto de uma ampla gama de arquivos. [Saiba
  mais](https://tika.apache.org/).
- **PostgreSQL**: O sistema de banco de dados relacional usado para armazenar
  informações estruturadas necessárias para a aplicação. [Saiba
  mais](https://www.postgresql.org/).
- **Kubernetes**: A plataforma base que utilizamos para rodar nossa aplicação,
  incluindo os componentes mencionados acima e a própria aplicação, gerenciada
  por meio de CronJobs para execução periódica de tarefas. [Saiba
  mais](https://kubernetes.io/).

Dentro do repositório do projeto, encontra-se o diretório `charts`, que contém
os arquivos do Helm chart necessários para fazer o deploy da aplicação no
Kubernetes, facilitando a gestão de pacotes e configurações.

É importante mencionar que para rodar todo o ambiente de desenvolvimento,
incluindo todos os componentes essenciais mencionados anteriormente, pode haver
um uso significativo dos recursos da máquina local. Isso inclui CPU, memória e
espaço em disco. Certifique-se de que sua máquina tenha recursos suficientes
para suportar a execução de um cluster Kubernetes com múltiplos pods, serviços
e volumes, para evitar qualquer degradação de desempenho durante o
desenvolvimento.

## Preparando o Ambiente de Desenvolvimento 

Se você deseja contribuir para o projeto, é essencial configurar o ambiente de
desenvolvimento corretamente. Para isso, você precisará instalar as seguintes
ferramentas:
- **Minikube**: Uma ferramenta que permite rodar um cluster Kubernetes local em
  sua máquina. Utilizamos o Minikube como ambiente de desenvolvimento padrão.
  [Saiba mais](https://minikube.sigs.k8s.io/docs/).
- **Tilt**: Uma ferramenta que automatiza e gerencia o ambiente de desenvolvimento,
  facilitando o desenvolvimento com containers. [Saiba mais](https://tilt.dev/).
- **Docker**: Uma plataforma de desenvolvimento que permite a criação, execução
  e compartilhamento de aplicações em containers. [Saiba
  mais](https://www.docker.com/).
- **ctlptl**: Uma ferramenta desenvolvida pelo time do Tolt que facilita a
  inicialização de um cluster Kubernetes e um container registry local. [Saiba
  mais](https://github.com/tilt-dev/ctlptl)
  

## Ambiente Padrão de Desenvolvimento com Minikube 

Para o desenvolvimento, escolhemos o Minikube como nossa ferramenta padrão.
Minikube é uma solução prática que simula um cluster Kubernetes diretamente no
seu computador. Isso simplifica enormemente o desenvolvimento e os testes de
aplicações feitas para Kubernetes, eliminando a necessidade de um cluster
físico ou virtual complexo. Com Minikube, você pode testar rapidamente as
alterações no código em um ambiente seguro e fechado, que reproduz fielmente um
ambiente de produção real. Essa prática assegura a compatibilidade da nossa
aplicação em diferentes configurações de Kubernetes. [Descubra mais sobre
Minikube aqui](https://minikube.sigs.k8s.io/docs/).

Embora o Minikube seja nossa escolha principal, você tem a liberdade de usar
qualquer ferramenta que prefira para montar seu cluster Kubernetes local,
contanto que ela esteja devidamente configurada em seu arquivo `kubeconfig`.
Mais adiante, você encontrará instruções sobre como configurar o contexto que o
Tilt usará para se conectar ao seu cluster. Caso você tenha somente um contexto
configurado, o Tilt operará como se estivesse apontando para um cluster
Minikube, adotando o contexto padrão, a menos que seja especificado outro.

## Configuração do Ambiente de Desenvolvimento

As seguintes ferramentas são essenciais para configurar e gerenciar o ambiente
de desenvolvimento:

### Kubernetes Local no Minikube configurado pelo ctlptl

O Minikube permite subir um cluster de Kubernetes localmente. Utilizamos
targets específicos no `Makefile` do projeto para esta finalidade. Por exemplo,
para iniciar o Minikube e configurar o ambiente de desenvolvimento, você pode
usar comandos como:

```bash 
make cluster
```

Esse comando ira executar o `ctlptl` para subir o cluster de Kubernetes local
utilizando o Minikube. E também ira configurar um container registry local para
armazenar as imagens Docker utilizadas no ambiente de desenvolvimento.

### Tilt

O Tilt automatiza e gerencia o ambiente de desenvolvimento, facilitando o
desenvolvimento com containers. Para iniciar, execute o comando `tilt up` no
terminal dentro do diretório do projeto:

```bash 
tilt up --stream
```

Isso inicia o Minikube e configura o ambiente localmente, simulando um ambiente
de produção no seu ambiente de desenvolvimento. Além disso, o tilt também vai
baixar arquivos de diário e um backup da base de dados e fazer o upload de tudo
no cluster para permitir que a aplicação já tenha algo para processar.

Uma vez que o tilt estiver rodando é possivel acessar uma intercace web com os
mesmos logs visiveis na linha de comando. A URL de acesso do interface é
[http://localhost:10350/](http://localhost:10350/)

### Configuração Flexível do Cluster

Embora o ambiente padrão utilize o Minikube, o Tilt permite a configuração para
usar outros clusters de Kubernetes, oferecendo flexibilidade para testes em
diferentes ambientes. Para isso, uma vez que você tenho o contexto de outro cluster
configurado em seu ambiente, basta utilizar a flag '--context':


```bash 
tilt up --stream --context=meucluster
```

### Atualizações Automáticas

Com o Tilt, o ambiente de desenvolvimento é atualizado automaticamente a cada
alteração de código, agilizando o processo de desenvolvimento e teste.

### Executando Comandos no OpenSearch com um Pod Temporário 

Para interagir com o OpenSearch diretamente de dentro do cluster Kubernetes, é
possível iniciar um pod temporário equipado com a ferramenta curl. Isso permite
executar comandos diretamente contra o OpenSearch. Utilize o seguinte comando
kubectl para criar um pod que será usado para essa interação:

```bash 
kubectl run opensearch-client --image=curlimages/curl:latest --restart=Never --rm -it -- /bin/sh
```

Este comando inicia um pod usando a imagem oficial curlimages/curl:latest,
que tem a ferramenta curl instalada. Após o pod ser iniciado e você obter
acesso ao shell dentro do pod, você pode executar comandos curl para interagir
com o OpenSearch. Aqui está um exemplo de comando curl que inclui a flag para
adicionar credenciais, que são definidas no arquivo YAML utilizado para subir o
cluster do OpenSearch:

```bash 
curl -XGET 'https://querido-diario-opensearsch-cluster.querido-diario.svc.cluster.local:9200/_cluster/health?pretty' -u 'admin:admin' --insecure
```
Neste comando:

`querido-diario-opensearsch-cluster.querido-diario.svc.cluster.local:9200` é a
URL padrão de acesso ao cluster OpenSearch. Se você customizar o deploy, talvez
seja necessário substituído pelo nome do serviço do OpenSearch dentro do seu
cluster Kubernetes. `admin:admin` também são as credencias padrão utilizadas no
OpenSearch do ambiente de desenvolvimento. Se essas credencias utlizadas forem
alteradas, o comando curl também deve utilizar as novas credenciaisde acesso ao
OpenSearch. Este comando curl faz uma requisição GET para verificar a saúde do
cluster OpenSearch, autenticando-se com as credenciais fornecidas. Mas qualquer
requisição ao cluster OpenSearch é possivel.

Após o uso, o pod será automaticamente removido do cluster, graças à flag --rm
utilizada no comando.

### Acesso ao Container Registry com o Tilt

Para o pleno funcionamento do Tilt, é necessário ter acesso a um container
registry, onde as imagens Docker da aplicação serão armazenadas e
posteriormente acessadas durante o processo de desenvolvimento e deploy. Em
nosso projeto, o registro de container utilizado é o configurado pelo `ctlptl` 
localmente. É possivel visualizar o container rodando o registry executando o
seguinte comando:

```bash
docker ps
```

Por padrão o nome do container configurado quando executados o `make cluster` é
`querido-diario-registry`. Tilt ira detectar automaticamente o container registry
configurado e utilizar para armazenar as imagens Docker.

# Comandos uteis durante o desenvolvimento

Nessa seção iremos listar alguns comandos uteis que podem ser utilizados durante
o desenvolvimento da aplicação. 

> **Nota**: Todos os comandos consideram a configuração padrão do ambiente de
> desenvolvimento. Caso você tenha feito alguma alteração, é necessário ajustar
> os comandos de acordo com a sua configuração.

## Acessando o banco de dados

Para acessar o banco de dados, você pode utilizar o comando `kubectl` para
executar um pod temporário com o cliente `psql` instalado. O comando a seguir
cria um pod temporário que executa o cliente `psql` e se conecta ao banco de
dados PostgreSQL:

```bash
kubectl run -it --rm --image=postgres:15 --restart=Never --env=PGPASSWORD=queridodiario psql --  psql --host=postgresql.postgresql.svc.cluster.local --username=queridodiario -d queridodiariodb
```

Este comando cria um pod temporário chamado `psql` que executa o cliente `psql`
e se conecta ao banco de dados PostgreSQL. O cliente `psql` é executado com o
usuário `queridodiario` e se conecta ao host `queridodiariodb`. Após a
conexão ser estabelecida, você pode executar comandos SQL diretamente no banco
de dados.

## Acessando o MinIO

Para acessar a interface web do MinIO que permite a visualização dos arquivos
armazenados, você pode acessar a porta que já é compartilhada pelo Tilt. Para isso 
é necessário obter as credenciais de acesso ao MinIO. Para isso, execute o seguinte
comando:

```bash
kubectl get secret --namespace minio minio -o jsonpath="{.data.root-user}" | base64 --decode
kubectl get secret --namespace minio minio -o jsonpath="{.data.root-password}" | base64 --decode
```

Depois acessar a página web em [localhost:9001](http://localhost:9001) e
informar as credenciais obtidas.

## Acessando o OpenSearch

Para acessar o OpenSearch, você pode utilizar o comando `kubectl` para executar
um pod temporário com o cliente `curl` instalado. O comando a seguir cria um
pod temporário que executa o cliente `curl` e se conecta ao OpenSearch:

```bash
kubectl run -it --rm --image=curlimages/curl:latest --restart=Never curl -- /bin/sh
```

Este comando cria um pod temporário chamado `curl` que executa o cliente `curl`
e se conecta ao OpenSearch. Após a conexão ser estabelecida, você pode executar
comandos `curl` para interagir com o OpenSearch. Por exemplo, você pode
executar um comando `curl` para verificar a saúde do cluster OpenSearch:

```bash
curl -XGET 'https://querido-diario-opensearsch-cluster.querido-diario.svc.cluster.local:9200/_cluster/health?pretty' -u 'admin:admin' --insecure
```

Este comando faz uma requisição `GET` para verificar a saúde do cluster
OpenSearch, autenticando-se com as credenciais fornecidas. Você pode executar
qualquer comando `curl` para interagir com o OpenSearch.

## Acessando o Apache Tika Server

Para acessar o Apache Tika Server, você pode utilizar o comando `kubectl` para
executar um pod temporário com o cliente `curl` instalado. O comando a seguir
cria um pod temporário que executa o cliente `curl` e se conecta ao Apache Tika
Server:

```bash
kubectl run -it --rm --image=curlimages/curl:latest --restart=Never curl -- /bin/sh
```
    
Este comando cria um pod temporário chamado `curl` que executa o cliente `curl`
e se conecta ao Apache Tika Server. Após a conexão ser estabelecida, você pode
executar comandos `curl` para enviar arquivos para o Apache Tika Server e
receber os metadados e texto extraídos. Por exemplo, você pode executar um
comando `curl` para enviar um arquivo PDF para o Apache Tika Server e receber
os metadados e texto extraídos:

```bash
# Apenas baixando um arquivo PDF para enviar para o Apache Tika Server
curl -XGET https://querido-diario.nyc3.cdn.digitaloceanspaces.com/2917359/2024-04-05/f6108244f24fdd6adc218fae72e8ce81fe30ca2b -o file.pdf
curl -T file.pdf http://tika.tika.svc.cluster.local:9998/meta
```

Este comando envia o arquivo PDF especificado para o Apache Tika Server e
recebe os metadados extraídos. Você pode executar qualquer comando `curl` para
enviar arquivos para o Apache Tika Server e receber os metadados e texto
extraídos.


---

Esperamos que este guia facilite o processo de configuração e contribuição para
o projeto. Caso tenha dúvidas ou necessite de assistência adicional, sinta-se à
vontade para consultar a documentação das ferramentas mencionadas ou entrar em
contato com a nossa equipe de desenvolvimento.
