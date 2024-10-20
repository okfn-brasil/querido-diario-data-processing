**English (US)** | [Português (BR)](/docs/CONTRIBUTING.md)

# Contributing
Querido Diario has a [Contribution Guide](https://docs.queridodiario.ok.org.br/en/latest/contributing/contribution-guide.html#contributing) that is relevant to all of its repositories. The guide provides general information about how to interact with the project, the code of conduct you adhere to when contributing, the list of ecosystem repositories and the first actions you can take. We recommend reading it before continuing.

Have you read it? Then let's move on to the specific information about this repository:
- [Some definitions](#some-definitions)
- [Structure](#structure)
- [How to set up the development environment](#how-to-set-up-the-development-environment)
    - [On Linux](#on-linux)
- [Maintaining](#maintaining)

## Some definitions

For us to speak the same language, we need to agree on some important terms for the project:

- Resources: Where data can be found and used (Postgres database, Opensearch engine, etc.);
- Services: Abstractions for accessing and modifying resources (OpensearchInterface, etc.) and other tools (ApacheTikaExtractor);
- Tasks: Unit (or step) of processing that usually interacts with resources to generate outputs;
- Pipelines: A set of tasks that fulfills a goal.

## Structure

A brief description of the repository structure:

| **Directory**                         | **Description**                                                                                              |
|---------------------------------------|--------------------------------------------------------------------------------------------------------------|
| [`.github`](/.github)                 | Repository settings for GitHub.                                                                              |
| [`docs`](/docs)                       | Repository documentation files (README, CONTRIBUTING, etc.).                                                 |
| [`config`](/config)                   | Configuration files such as environment variables and thematic index keywords.                               |
| [`data_extraction`](/data_extraction) | Interfaces and implementations of services for interacting with data extractors like Apache Tika (text).     |
| [`database`](/database)               | Interfaces and implementations of services for interacting with databases like Postgres.                     |
| [`docs`](/docs)                       | Repository documentation files (README, CONTRIBUTING, etc.).                                                 |
| [`index`](/index)                     | Interfaces and implementations of services for interacting with search engines like Opensearch.              |
| [`main`](/main)                       | Processing pipelines (to initially understand the project's operation, this is a good starting point).       |
| [`segmentation`](/segmentation)       | Implementation of text segmenters for diaries (e.g.: 1 municipal association diary -> N municipal diaries).  |
| [`storage`](/storage)                 | Interfaces and implementations of services for interacting with object storage like Minio.                   |
| [`tasks`](/tasks)                     | Directory containing tasks to be executed in the pipelines (task definitions are found in their docstrings). |
| [`tasks/utils`](/tasks/utils)         | Utilities to assist tasks.                                                                                   |
| [`tests`](/tests)                     | Unit and integration tests (👀).                                                                             |


## How to set up the development environment

To set up the development environment, you need the [podman](https://podman.io/) container manager and Python (3.8+).

### On Linux

Before anything else, we use `pre-commit` in the project, so don’t forget to set up a Python virtual environment with it.

1. With Python and podman installed, in the root of the repository, activate the virtual environment:

```console
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the development dependencies and install `pre-commit`:

```console
pip install -r requirements-dev.txt
pre-commit install
```

3. Now let's build the images and set up the pod and the resource containers used in the processing:

```console
make build
make setup
```

If you want the processed data to be consumed by the local [Querido Diário API](https://github.com/okfn-brasil/querido-diario-api/) or [Backend](https://github.com/okfn-brasil/querido-diario-backend/), check the [end-to-end setup documentation](https://docs.queridodiario.ok.org.br/en/latest/contributing/end-to-end-configuration.html). In this case, the setup should be done using:

```console
make build
FULL_PROJECT=true make setup
```

4. Done! Now you can start editing the code and running the pipelines.

# Maintaining
Maintainers must follow the guidelines in Querido Diário's [Guide for Maintainers](https://docs.queridodiario.ok.org.br/en/latest/contributing/contribution-guide.html#maintaining).
