**Português (BR)** | [English (US)](/docs/FAQ-en-US.md)

# Perguntas frequentes (FAQ)

Respostas curtas para as dúvidas mais comuns sobre este repositório. Para o passo a passo completo, consulte o [README](/docs/README.md) e o [CONTRIBUTING.md](/docs/CONTRIBUTING.md). Não encontrou sua dúvida? Veja a seção [Suporte](/docs/SUPPORT.md).

- [Sobre o projeto](#sobre-o-projeto)
- [Instalação](#instalação)
- [Execução](#execução)
- [Troubleshooting](#troubleshooting)
- [Contribuição](#contribuição)

## Sobre o projeto

### O que este repositório faz?

Ele processa os diários oficiais coletados pelos raspadores: extrai o texto dos arquivos (PDF, DOC, DOCX, ODT etc.) com o Apache Tika, salva o texto em `.txt` no armazenamento de objetos, indexa o conteúdo no OpenSearch e gera índices temáticos com excertos dos diários. As etapas do pipeline principal estão descritas no [README](/docs/README.md#como-executar).

### Como ele se relaciona com os outros repositórios do Querido Diário?

Ele fica entre a coleta e a consulta:

1. os [raspadores](https://github.com/okfn-brasil/querido-diario) gravam os metadados dos diários no Postgres (tabelas `gazettes` e `territories`) e os arquivos no armazenamento de objetos;
2. este repositório lê esses dados, extrai os textos e popula o OpenSearch;
3. a [API](https://github.com/okfn-brasil/querido-diario-api) e o [Backend](https://github.com/okfn-brasil/querido-diario-backend) consultam o que foi indexado.

Veja o [ecossistema do Querido Diário](https://docs.queridodiario.ok.org.br/pt-br/latest/contribuindo/guia-de-contribuicao.html#ecossistema-do-querido-diario).

### Quais serviços o ambiente usa?

Todos são definidos no [`docker-compose.yml`](/docker-compose.yml):

| **Serviço**   | **Papel**                                         | **Porta no host** (variável)                      |
|---------------|---------------------------------------------------|---------------------------------------------------|
| `postgres`    | Metadados dos diários e dos territórios           | `5432` (`POSTGRES_PORT`)                          |
| `minio`       | Armazenamento de objetos compatível com S3        | `9000` (`STORAGE_PORT`)                           |
| `opensearch`  | Motor de busca (índice principal e temáticos)     | `9200` e `9300` (`OPENSEARCH_PORT1`, `OPENSEARCH_PORT2`) |
| `apache-tika` | Extração de texto dos arquivos                    | não é publicada no host                           |
| `app`         | Imagem deste repositório, onde os pipelines rodam | —                                                 |

### O que são diários de associações e segmentadores?

Algumas associações de municípios publicam um único diário com atos de vários municípios. Esses diários são identificados por um `territory_id` terminado em `00000` (ex.: `2700000` para Alagoas). Um segmentador, em [`segmentation/`](/segmentation), divide o texto em um diário por município. Hoje só a associação de Alagoas tem segmentador ([#77](https://github.com/okfn-brasil/querido-diario-data-processing/issues/77)).

## Instalação

### Quais são os pré-requisitos?

- `make`, `docker` e o plugin `docker compose`: todos os alvos do [`Makefile`](/Makefile) chamam `docker` e `docker compose` diretamente;
- Python, somente para usar o `pre-commit` (veja [Contribuição](#contribuição));
- espaço em disco para as imagens: num teste em arm64, a imagem da aplicação ocupou cerca de 2,3 GB, a do OpenSearch cerca de 2,1 GB e a do Tika cerca de 570 MB.

### Posso usar podman em vez de Docker?

O README cita o [podman](https://podman.io/), mas o `Makefile` atual executa `docker` e `docker compose`. Com podman, esses comandos precisam estar disponíveis no seu sistema. O fluxo desta FAQ foi validado apenas com Docker.

### Como monto o ambiente?

Na raiz do repositório:

```console
make build
make setup
```

- `make build` constrói a imagem da aplicação (a partir da imagem base publicada em `ghcr.io`) e a imagem do Apache Tika, para a arquitetura da sua máquina (`make build amd64=1` ou `make build arm64=1` forçam uma arquitetura).
- `make setup` copia `config/sample.env` para `envvars` (se ainda não existir) e sobe `postgres`, `opensearch`, `minio` e `apache-tika`.

Detalhes em ["como configurar o ambiente de desenvolvimento"](/docs/CONTRIBUTING.md#como-configurar-o-ambiente-de-desenvolvimento). Se algo falhar, veja [Troubleshooting](#troubleshooting).

### O `make setup` apaga meus dados?

Sim. Antes de subir os serviços, ele executa `docker compose down --volumes --remove-orphans` (alvo `destroy-services`), que remove os volumes do Postgres, do OpenSearch e do MinIO. O mesmo vale para `make run` e `make test`, que chamam `make setup`/`create-services`. Para executar de novo sem recriar o ambiente, use os alvos `re-*`, como `make re-run` e `make retest`.

### Onde ficam as configurações?

No arquivo `envvars`, criado a partir de [`config/sample.env`](/config/sample.env) e ignorado pelo git. Ele é carregado no container `app`. Principais variáveis:

| **Variável**                                           | **Uso**                                                                      |
|--------------------------------------------------------|------------------------------------------------------------------------------|
| `POSTGRES_*`                                           | Conexão com o banco de metadados                                             |
| `STORAGE_*`                                            | Armazenamento de objetos (sem `STORAGE_ENDPOINT`, usa o endpoint padrão da AWS S3) |
| `OPENSEARCH_*`                                         | Conexão e nome do índice principal (`querido-diario`)                        |
| `APACHE_TIKA_SERVER`                                   | Endereço do Tika                                                             |
| `EXECUTION_MODE`                                       | Quais diários processar: `ALL`, `DAILY` ou `UNPROCESSED`                     |
| `DEBUG`                                                | `1` ativa logs de depuração                                                  |
| `TIKA_*`, `MEMORY_LIMIT_BYTES`, `MAX_GAZETTE_FILE_SIZE_MB`, `GAZETTE_QUERY_PAGE_SIZE` | Ajustes de robustez e memória (veja [Troubleshooting](#troubleshooting)) |
| `USE_RELATIVE_FILE_PATHS`                              | `true` grava caminhos relativos em vez de URLs completas no índice           |

As portas expostas no host podem ser alteradas por variáveis de ambiente do shell, por exemplo `POSTGRES_PORT=5433 make setup`.

### Funciona em macOS, Apple Silicon ou Windows?

- **macOS**: funciona com Docker Desktop, mas `make setup` falha ao copiar o `envvars` (veja [Troubleshooting](#troubleshooting)).
- **Apple Silicon (arm64)**: o `make build` detecta a arquitetura e constrói imagens arm64. Rode-o antes do `make setup`: se o compose construir a imagem do Tika por conta própria, ele usa `PLATFORM=linux/amd64` como padrão e a imagem roda emulada.
- **Windows**: não há suporte oficial; o projeto roda principalmente em Linux ([#39](https://github.com/okfn-brasil/querido-diario-data-processing/pull/39)). O WSL é a alternativa mais próxima ([#71](https://github.com/okfn-brasil/querido-diario-data-processing/issues/71)).

### Como desligo e limpo o ambiente?

```console
make destroy-services
```

Ele remove containers, volumes e a rede do projeto. As imagens construídas continuam no Docker; para remover a da aplicação, use `make destroy`.

## Execução

### Como alimento o banco e o armazenamento com diários?

Este repositório não cria as tabelas `gazettes` e `territories`: elas são criadas e populadas pelos [raspadores](https://github.com/okfn-brasil/querido-diario), que também enviam os arquivos ao armazenamento ([#42](https://github.com/okfn-brasil/querido-diario-data-processing/issues/42)). Siga a [configuração de ponta a ponta](https://docs.queridodiario.ok.org.br/pt-br/latest/contribuindo/configuracao-de-ponta-a-ponta.html#gerando-dados-com-os-raspadores) e aponte os raspadores para os mesmos serviços usados aqui:

| **Raspadores** (`querido_diario_raspadores/gazette/settings.py`) | **Este repositório** (`envvars`) |
|---------------------------------------------------|-----------------------------------------------------------------------------|
| `QUERIDODIARIO_DATABASE_URL`                      | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB` |
| `FILES_STORE`                                     | `STORAGE_BUCKET`                                                            |
| `AWS_ENDPOINT_URL`                                | `STORAGE_ENDPOINT`                                                          |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`      | `STORAGE_ACCESS_KEY`, `STORAGE_ACCESS_SECRET`                               |
| `AWS_REGION_NAME`                                 | `STORAGE_REGION`                                                            |

Se você tiver um dump do banco, `make load-database` o restaura no Postgres. O arquivo padrão é `data/queridodiariodb.tar`; para usar outro, rode `make load-database DATABASE_RESTORE_FILE=caminho/do/dump.tar`.

### Como executo os pipelines?

| **Comando**                                                  | **Pipeline**                                                                |
|--------------------------------------------------------------|-----------------------------------------------------------------------------|
| `make re-run`                                                | `gazette_texts`: extração de texto, indexação e índices temáticos           |
| `make run`                                                   | `make setup` seguido de `make re-run` (recria o ambiente e apaga os dados)  |
| `make aggregate-gazettes`                                    | `aggregates`: agrega os textos por município/estado e ano                   |
| `docker compose run --rm app python main -p embedding_rerank` | `embedding_rerank`: recalcula o score semântico de excertos que ficaram sem score |

### Como escolho quais diários processar?

Pela variável `EXECUTION_MODE` no `envvars`:

- `ALL`: todos os diários (valor do `config/sample.env`);
- `DAILY`: diários coletados nas últimas 24 horas (padrão do código quando a variável não está definida);
- `UNPROCESSED`: diários ainda não marcados como processados no banco.

Nos três modos, arquivos `.zip` são ignorados e os diários mais recentes no banco são processados primeiro.

### Onde vejo os resultados?

- **OpenSearch**: índice principal `querido-diario` e um índice por tema (hoje `ambiental` e `educacao`). Para listar: `curl -u admin:admin "http://localhost:9200/_cat/indices?v"`.
- **Armazenamento de objetos**: um `.txt` ao lado de cada arquivo de diário e, depois de `make aggregate-gazettes`, os agregados compactados em `aggregates/<UF>/`.
- **Banco**: a coluna `processed` da tabela `gazettes`. Use `make sql` para abrir o `psql` e `make shell` para abrir um shell no container da aplicação.

Mais dicas na [documentação de ponta a ponta](https://docs.queridodiario.ok.org.br/pt-br/latest/contribuindo/configuracao-de-ponta-a-ponta.html#dicas-de-uso-do-ambiente).

### Como adiciono ou altero um tema?

Os temas ficam em [`config/themes_config.json`](/config/themes_config.json). Cada tema define `name`, `index` (nome do índice no OpenSearch), `queries`, `stopwords` e `entities`. O pipeline `gazette_texts` cria o índice do tema se ele ainda não existir.

## Troubleshooting

Os itens de `cp: illegal option` até `relation "territories" does not exist`, além do último (`make retest`), foram reproduzidos ao montar o ambiente com Docker Desktop em macOS (arm64). Os demais vêm das issues e do código. Vários são contornados com um arquivo `docker-compose.override.yml` na raiz do repositório. O `docker compose` lê esse arquivo automaticamente, então não é preciso alterar o `docker-compose.yml`. Não faça commit dele.

### `cp: illegal option -- -` e `env file .../envvars not found`

O alvo `set-run-variable-values` usa `cp --update=none`, uma opção do GNU `cp` que o `cp` do macOS não tem. O erro é ignorado (`|| true`), mas o `envvars` não é criado e o `docker compose` falha em seguida. Crie o arquivo manualmente e rode o comando de novo:

```console
cp -n config/sample.env envvars
make setup
```

### Erro `401 UNAUTHORIZED` ao baixar a imagem do MinIO

Em outubro de 2026, as imagens públicas do MinIO deixaram de ser baixadas sem autenticação: o pull de `quay.io/minio/minio:RELEASE.2025-09-07T16-13-09Z` (a usada no `docker-compose.yml`) falha com `401 UNAUTHORIZED`, e `minio/minio` no Docker Hub responde `pull access denied`. Se você já tiver uma imagem do MinIO no cache local do Docker, ou quiser usar outro serviço compatível com S3, aponte para ela no `docker-compose.override.yml`:

```yaml
services:
  minio:
    image: <imagem-compatível-com-s3-disponível-localmente>
```

### O bucket `queridodiariobucket` não existe

A imagem oficial do MinIO não cria buckets a partir de `MINIO_DEFAULT_BUCKETS`, e o serviço `minio-createbucket` não é iniciado pelo `make setup`. Crie o bucket com o `mc` que vem na imagem do servidor:

```console
docker compose exec minio sh -c 'mc alias set local http://localhost:9000 minio-access-key minio-secret-key && mc mb --ignore-existing local/queridodiariobucket'
```

### `dependency failed to start: container ...-apache-tika-1 is unhealthy`

Os alvos que usam `docker compose run app` (`make re-run`, `make retest`, `make shell` etc.) esperam o Tika ficar saudável, mas o healthcheck chama `curl`, que não está instalado na imagem do Tika. Além disso, o `command` do serviço não passa `--host 0.0.0.0`, então o Tika só aceita conexões de dentro do próprio container. Corrija as duas coisas no `docker-compose.override.yml`:

```yaml
services:
  apache-tika:
    command: java -jar /tika-server.jar --host 0.0.0.0
    healthcheck:
      test: ["CMD", "bash", "-c", "echo > /dev/tcp/localhost/9998"]
```

Depois, recrie o serviço com `docker compose up -d apache-tika`.

### `Connection refused` para `localhost:9200`, `localhost:9998` ou `127.0.0.1:9000`

O `config/sample.env` aponta para `localhost`, que dentro do container `app` é o próprio container. O compose só corrige o `POSTGRES_HOST`. Para rodar os pipelines dentro do compose, use os nomes dos serviços no `envvars`:

```
STORAGE_ENDPOINT=http://minio:9000
OPENSEARCH_HOST=http://opensearch:9200
APACHE_TIKA_SERVER=http://apache-tika:9998
```

### `psycopg2.errors.UndefinedTable: relation "territories" does not exist`

O banco está vazio. Popule-o com os raspadores ou com um dump (veja [Como alimento o banco e o armazenamento com diários?](#execução)).

### O build do Tika falha ou o container mostra `Invalid or corrupt jarfile /tika-server.jar`

Esse problema ([#73](https://github.com/okfn-brasil/querido-diario-data-processing/issues/73)) foi corrigido em [#123](https://github.com/okfn-brasil/querido-diario-data-processing/pull/123): o JAR passou a ser baixado de `archive.apache.org`, que mantém todas as versões. Atualize sua branch. Para usar outra versão, rode `make build-tika-server TIKA_VERSION=x.y.z`.

### O processo fica sem memória (OOM, `MemoryError`)

Arquivos grandes podem esgotar a memória ([#25](https://github.com/okfn-brasil/querido-diario-data-processing/issues/25), [#6](https://github.com/okfn-brasil/querido-diario-data-processing/issues/6)). Ajustes disponíveis no `envvars`:

- `MEMORY_LIMIT_BYTES`: o pipeline limita o próprio espaço de endereçamento (`RLIMIT_AS`) a 75% (soft) e 90% (hard) desse valor, que por padrão é 2 GB;
- `MAX_GAZETTE_FILE_SIZE_MB` (padrão `500`): arquivos maiores são ignorados;
- `GAZETTE_QUERY_PAGE_SIZE` (padrão `1000`): quantos diários são lidos do banco por vez;
- `TIKA_CHUNK_SIZE` (padrão `8192` bytes): tamanho dos blocos enviados ao Tika.

Para a memória do próprio Tika e do OpenSearch, veja o [guia de monitoramento](/docs/MONITORING_GUIDE.md).

### `TransportError(413, '')` ao indexar no OpenSearch

O documento excede o tamanho máximo de requisição do OpenSearch (`http.max_content_length`). O caso está em investigação em [#112](https://github.com/okfn-brasil/querido-diario-data-processing/issues/112); o [guia de monitoramento](/docs/MONITORING_GUIDE.md#opensearch-lento-ou-falhando) mostra como aumentar o limite.

### `ChunkedEncodingError`, `IncompleteRead` ou requisições lentas ao Tika

Veja o [guia de monitoramento](/docs/MONITORING_GUIDE.md#investigando-problemas-específicos). Ele explica como achar os arquivos problemáticos nos logs. As tentativas são controladas por `TIKA_MAX_RETRIES` (padrão `5`) e `TIKA_RETRY_BASE_DELAY` (padrão `2.0` segundos).

### Diários de associação falham com `KeyError` em `segmentation/factory.py`

Todo diário com `territory_id` terminado em `00000` é tratado como diário de associação e precisa de um segmentador registrado. Hoje só existe o de Alagoas (`2700000`); os demais estão nas issues [#83 a #98](https://github.com/okfn-brasil/querido-diario-data-processing/issues?q=is%3Aissue+segmentador) ([#77](https://github.com/okfn-brasil/querido-diario-data-processing/issues/77)). Veja [Como adiciono um segmentador?](#contribuição).

### O texto extraído tem caracteres quebrados (ex.: `Ã©`)

Problema conhecido e ainda em aberto ([#76](https://github.com/okfn-brasil/querido-diario-data-processing/issues/76)).

### `make retest` mostra dezenas de erros

`make retest` roda todos os módulos de `tests/`, e alguns têm falhas conhecidas ([#57](https://github.com/okfn-brasil/querido-diario-data-processing/issues/57)): eles esperam serviços em `localhost` ou usam APIs antigas de mock e do `opensearch-py`. A CI roda apenas os arquivos `tests/*_tests.py`, com o [`instrumented_test_runner.py`](/instrumented_test_runner.py). Veja [Como rodo os testes?](#contribuição).

## Contribuição

### Por onde começo?

Leia o [Guia para Contribuição](https://docs.queridodiario.ok.org.br/pt-br/latest/contribuindo/guia-de-contribuicao.html#contribuindo) do Querido Diário e o [CONTRIBUTING.md](/docs/CONTRIBUTING.md) deste repositório. Issues com o rótulo [`good first issue`](https://github.com/okfn-brasil/querido-diario-data-processing/issues?q=is%3Aopen+label%3A%22good+first+issue%22) são um bom ponto de partida.

### Como configuro o lint?

O projeto usa `pre-commit` com `ruff` (ordenação de imports e formatação) e verificações básicas, como conflitos de merge e chaves privadas. Veja [`.pre-commit-config.yaml`](/.pre-commit-config.yaml).

```console
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
```

O `requirements-dev.txt` inclui o `requirements.txt` (com `sentence-transformers`), então a instalação é pesada. A CI roda `pre-commit run --all-files` em todo PR para a `main`.

### Como rodo os testes?

A CI ([`lint_and_unit.yaml`](/.github/workflows/lint_and_unit.yaml)) sobe Postgres, OpenSearch, MinIO e Tika e roda:

```console
python instrumented_test_runner.py
```

Esse script executa apenas `tests/*_tests.py`. Com os serviços no ar (`make setup`), rode-o dentro do compose:

```console
docker compose run --rm --no-deps app python instrumented_test_runner.py
```

Os testes de extração em `tests/text_extraction_tests.py` esperam o Tika em `http://localhost:9998`, porta que o compose não publica, e falham nesse modo. Para rodá-los também, use a rede do container do Tika (o nome do container depende do nome da pasta do projeto). Assim, os 41 testes passaram:

```console
docker run --rm --network container:querido-diario-data-processing-apache-tika-1 \
  -v "$PWD":/mnt/code -w /mnt/code -e PYTHONPATH=/mnt/code \
  okfn-brasil/querido-diario-data-processing:latest python instrumented_test_runner.py
```

Também existem alvos por módulo: `make retest-tika`, `make retest-tasks`, `make retest-main`, `make retest-index`, `make retest-postgres` e `make retest-digital-ocean-spaces`.

### Como adiciono um segmentador de associação?

1. Crie uma classe em [`segmentation/segmenters/`](/segmentation/segmenters) que herde de `AssociationSegmenter` ([`segmentation/base`](/segmentation/base)) e implemente `get_gazette_segments`. Use [`al_associacao_municipios.py`](/segmentation/segmenters/al_associacao_municipios.py) como referência.
2. Exporte a classe em [`segmentation/segmenters/__init__.py`](/segmentation/segmenters/__init__.py).
3. Registre o `territory_id` da associação (terminado em `00000`) no dicionário `territory_to_segmenter_class` em [`segmentation/factory.py`](/segmentation/factory.py).

### Qual o padrão de commits e PRs?

As mensagens de commit seguem o formato `tipo: descrição` em português (`feat:`, `fix:`, `docs:`, `ci:` etc.), como no histórico do repositório. Todo PR para a `main` passa pelo lint e pelos testes da CI. Um comentário com `cicd/build` no PR dispara os workflows de build das imagens. As pessoas mantenedoras seguem o [Guia para Mantenedoras](https://docs.queridodiario.ok.org.br/pt-br/latest/contribuindo/guia-de-contribuicao.html#mantendo).

### Onde peço ajuda?

No [Discord da comunidade](https://go.ok.org.br/discord) (veja [SUPPORT.md](/docs/SUPPORT.md)) ou abrindo uma [issue](https://github.com/okfn-brasil/querido-diario-data-processing/issues).
