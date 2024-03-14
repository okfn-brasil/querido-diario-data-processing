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

### Kubernetes Local com Minikube

O Minikube permite subir um cluster de Kubernetes localmente. Utilizamos
targets específicos no `Makefile` do projeto para esta finalidade. Por exemplo,
para iniciar o Minikube e configurar o ambiente de desenvolvimento, você pode
usar comandos como:

```bash 
make cluster
```

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

---

Esperamos que este guia facilite o processo de configuração e contribuição para
o projeto. Caso tenha dúvidas ou necessite de assistência adicional, sinta-se à
vontade para consultar a documentação das ferramentas mencionadas ou entrar em
contato com a nossa equipe de desenvolvimento.
