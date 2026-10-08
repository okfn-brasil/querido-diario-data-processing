**Português (BR)** | [English (US)](/docs/CONTRIBUTING-en-US.md)

# Contribuindo
O Querido Diário possui um [Guia para Contribuição](https://docs.queridodiario.ok.org.br/pt-br/latest/contribuindo/guia-de-contribuicao.html#contribuindo) principal que é relevante para todos os seus repositórios. Este guia traz informações gerais sobre como interagir com o projeto, o código de conduta que você adere ao contribuir, a lista de repositórios do ecossistema e as primeiras ações que você pode tomar. Recomendamos sua leitura antes de continuar.

Já leu? Então vamos às informações específicas deste repositório:
- [Algumas definições](#algumas-definições)
- [Estrutura](#estrutura)
- [Como configurar o ambiente de desenvolvimento](#como-configurar-o-ambiente-de-desenvolvimento)
    - [Em Linux](#em-linux)
- [Mantendo](#mantendo)

## Algumas definições

Para que possamos falar a mesma língua, precisamos pactuar alguns termos importantes para o projeto:

- Recursos: Onde dados podem ser encontrados e utilizados (banco Postgres, motor de busca Opensearch, etc.);
- Serviços: Abstrações para acesso e modificação de recursos (OpensearchInterface, etc.) e outras ferramentas (ApacheTikaExtractor);
- Tasks (ou tarefas): Unidade (ou etapa) de processamento que geralmente interage com os recursos para gerar suas saídas;
- Pipelines: Conjunto de tarefas que cumpre um objetivo.

## Estrutura

Uma breve descrição da estrutura do repositório:

| **Diretório**                         | **Descrição**                                                                                                                    |
|---------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| [`.github`](/.github)                 | Configurações do repositório para o GitHub.                                                                                      |
| [`docs`](/docs)                       | Arquivos de documentação do repositório (README, CONTRIBUTING, etc.).                                                            |
| [`config`](/config)                   | Arquivos de configuração como variáveis de ambiente e palavras-chave de índices temáticos.                                       |
| [`data_extraction`](/data_extraction) | Interfaces e implementações de serviços de interação com extratores de dados como o Apache Tika (texto).                         |
| [`database`](/database)               | Interfaces e implementações de serviços de interação com banco como o Postgres.                                                  |
| [`docs`](/docs)                       | Arquivos de documentação do repositório (README, CONTRIBUTING, etc.).                                                            |
| [`index`](/index)                     | Interfaces e implementações de serviços de interação com motores de busca como o Opensearch.                                     |
| [`main`](/main)                       | Pipelines de processamento (para compreender inicialmente o funcionamento do projeto este é um bom ponto de partida).            |
| [`segmentation`](/segmentation)       | Implementação de segmentadores do conteúdo textual de diários (ex: 1 diário de associação municipal -> N diários de municípios). |
| [`storage`](/storage)                 | Interfaces e implementações de serviços de interação com armazenamento de objetos como o Minio.                                  |
| [`tasks`](/tasks)                     | Diretório que contém as tarefas que serão executadas nos pipelines (definições das tarefas são encontradas em suas docstrings).  |
| [`tasks/utils`](/tasks/utils)         | Utilitários para auxiliar as tarefas.                                                                                            |
| [`tests`](/tests)                     | Testes unitários e de integração (👀).                                                                                           |


## Como configurar o ambiente de desenvolvimento

Para configurar o ambiente de desenvolvimento, é necessário o gestor de containers [podman](https://podman.io/) e Python (3.8+).

### Em Linux

Antes de qualquer coisa, utilizamos `pre-commit` no projeto, então não se esqueça de configurar de um ambiente virtual Python com ele.

1. Com o Python e podman instalados, na raíz do repositório, ative o ambiente virtual:

```console
python3 -m venv .venv
source .venv/bin/activate
```

2. Instale as dependências de desenvolvimento e instale o `pre-commit`:

```console
pip install -r requirements-dev.txt
pre-commit install
```

3. Agora vamos construir as imagens e montar o pod e os containers de recursos utilizados no processamento:

```console
make build
make setup
```

Caso deseje que os dados processados sejam consumidos pela [API](https://github.com/okfn-brasil/querido-diario-api/) ou [Backend](https://github.com/okfn-brasil/querido-diario-backend/) do Querido Diário localmente, acesse a documentação da [configuração de ponta-a-ponta](https://docs.queridodiario.ok.org.br/pt-br/latest/contribuindo/configuracao-de-ponta-a-ponta.html). Assim, a configuração deve ser feita usando:

```console
make build
FULL_PROJECT=true make setup
```

4. Pronto! Agora você já pode começar a editar o código e executar os pipelines.

Se algo der errado na configuração, na execução ou nos testes, consulte as [perguntas frequentes (FAQ)](/docs/FAQ.md).

# Mantendo
As pessoas mantenedoras devem seguir as diretrizes do [Guia para Mantenedoras](https://docs.queridodiario.ok.org.br/pt-br/latest/contribuindo/guia-de-contribuicao.html#mantendo) do Querido Diário.
