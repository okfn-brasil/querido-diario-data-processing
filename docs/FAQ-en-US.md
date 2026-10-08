**English (US)** | [Português (BR)](/docs/FAQ.md)

# Frequently asked questions (FAQ)

Short answers to the most common questions about this repository. For the full walkthrough, see the [README](/docs/README-en-US.md) and [CONTRIBUTING.md](/docs/CONTRIBUTING-en-US.md). Didn't find your question? Check [Support](/docs/SUPPORT-en-US.md).

- [About the project](#about-the-project)
- [Installation](#installation)
- [Running](#running)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## About the project

### What does this repository do?

It processes the gazettes collected by the scrapers. It extracts text from the files (PDF, DOC, DOCX, ODT, etc.) with Apache Tika, saves the text as `.txt` in object storage, indexes the content in OpenSearch and builds thematic indexes with gazette excerpts. The steps of the main pipeline are described in the [README](/docs/README.md#como-executar) (Portuguese).

### How does it relate to the other Querido Diário repositories?

It sits between collection and querying:

1. the [scrapers](https://github.com/okfn-brasil/querido-diario) write gazette metadata to Postgres (`gazettes` and `territories` tables) and the files to object storage;
2. this repository reads that data, extracts the texts and populates OpenSearch;
3. the [API](https://github.com/okfn-brasil/querido-diario-api) and the [Backend](https://github.com/okfn-brasil/querido-diario-backend) query what was indexed.

See the [Querido Diário ecosystem](https://docs.queridodiario.ok.org.br/en/latest/contributing/contribution-guide.html#ecosystem).

### Which services does the environment use?

They are all defined in [`docker-compose.yml`](/docker-compose.yml):

| **Service**   | **Role**                                             | **Host port** (variable)                          |
|---------------|------------------------------------------------------|---------------------------------------------------|
| `postgres`    | Gazette and territory metadata                       | `5432` (`POSTGRES_PORT`)                          |
| `minio`       | S3-compatible object storage                         | `9000` (`STORAGE_PORT`)                           |
| `opensearch`  | Search engine (main and thematic indexes)            | `9200` and `9300` (`OPENSEARCH_PORT1`, `OPENSEARCH_PORT2`) |
| `apache-tika` | Text extraction from files                           | not published on the host                         |
| `app`         | This repository's image, where the pipelines run     | —                                                 |

### What are association gazettes and segmenters?

Some associations of municipalities publish a single gazette with acts from several municipalities. These gazettes are identified by a `territory_id` ending in `00000` (e.g. `2700000` for Alagoas). A segmenter, in [`segmentation/`](/segmentation), splits that text into one gazette per municipality. Currently only the Alagoas association has a segmenter ([#77](https://github.com/okfn-brasil/querido-diario-data-processing/issues/77)).

## Installation

### What are the prerequisites?

- `make`, `docker` and the `docker compose` plugin: every target in the [`Makefile`](/Makefile) calls `docker` and `docker compose` directly;
- Python, only to use `pre-commit` (see [Contributing](#contributing));
- disk space for the images: in a test on arm64, the application image took about 2.3 GB, OpenSearch about 2.1 GB and Tika about 570 MB.

### Can I use podman instead of Docker?

The README mentions [podman](https://podman.io/), but the current `Makefile` runs `docker` and `docker compose`. With podman, those commands must be available on your system. The steps in this FAQ were validated with Docker only.

### How do I set up the environment?

From the repository root:

```console
make build
make setup
```

- `make build` builds the application image (from the base image published on `ghcr.io`) and the Apache Tika image for your machine's architecture (`make build amd64=1` or `make build arm64=1` force one).
- `make setup` copies `config/sample.env` to `envvars` (if it doesn't exist yet) and starts `postgres`, `opensearch`, `minio` and `apache-tika`.

Details in ["how to set up the development environment"](/docs/CONTRIBUTING-en-US.md#how-to-set-up-the-development-environment). If something fails, see [Troubleshooting](#troubleshooting).

### Does `make setup` delete my data?

Yes. Before starting the services, it runs `docker compose down --volumes --remove-orphans` (the `destroy-services` target), which removes the Postgres, OpenSearch and MinIO volumes. The same applies to `make run` and `make test`, which call `make setup`/`create-services`. To run again without recreating the environment, use the `re-*` targets, such as `make re-run` and `make retest`.

### Where is the configuration?

In the `envvars` file, created from [`config/sample.env`](/config/sample.env) and ignored by git. It is loaded into the `app` container. Main variables:

| **Variable**                                           | **Purpose**                                                                  |
|--------------------------------------------------------|------------------------------------------------------------------------------|
| `POSTGRES_*`                                           | Connection to the metadata database                                          |
| `STORAGE_*`                                            | Object storage (without `STORAGE_ENDPOINT`, the default AWS S3 endpoint is used) |
| `OPENSEARCH_*`                                         | Connection and main index name (`querido-diario`)                            |
| `APACHE_TIKA_SERVER`                                   | Tika address                                                                 |
| `EXECUTION_MODE`                                       | Which gazettes to process: `ALL`, `DAILY` or `UNPROCESSED`                   |
| `DEBUG`                                                | `1` enables debug logs                                                       |
| `TIKA_*`, `MEMORY_LIMIT_BYTES`, `MAX_GAZETTE_FILE_SIZE_MB`, `GAZETTE_QUERY_PAGE_SIZE` | Reliability and memory tuning (see [Troubleshooting](#troubleshooting)) |
| `USE_RELATIVE_FILE_PATHS`                              | `true` stores relative paths instead of full URLs in the index               |

Host ports can be changed with shell environment variables, e.g. `POSTGRES_PORT=5433 make setup`.

### Does it work on macOS, Apple Silicon or Windows?

- **macOS**: works with Docker Desktop, but `make setup` fails to copy `envvars` (see [Troubleshooting](#troubleshooting)).
- **Apple Silicon (arm64)**: `make build` detects the architecture and builds arm64 images. Run it before `make setup`: if compose builds the Tika image on its own, it defaults to `PLATFORM=linux/amd64` and the image runs under emulation.
- **Windows**: not officially supported; the project runs mainly on Linux ([#39](https://github.com/okfn-brasil/querido-diario-data-processing/pull/39)). WSL is the closest alternative ([#71](https://github.com/okfn-brasil/querido-diario-data-processing/issues/71)).

### How do I shut down and clean up the environment?

```console
make destroy-services
```

It removes the project's containers, volumes and network. Built images stay in Docker; to remove the application image, use `make destroy`.

## Running

### How do I feed the database and storage with gazettes?

This repository does not create the `gazettes` and `territories` tables: they are created and populated by the [scrapers](https://github.com/okfn-brasil/querido-diario), which also upload the files to storage ([#42](https://github.com/okfn-brasil/querido-diario-data-processing/issues/42)). Follow the [end-to-end setup](https://docs.queridodiario.ok.org.br/en/latest/contributing/end-to-end-configuration.html#generating-data-with-spiders) and point the scrapers to the same services used here:

| **Scrapers** (`querido_diario_raspadores/gazette/settings.py`) | **This repository** (`envvars`) |
|---------------------------------------------------|-----------------------------------------------------------------------------|
| `QUERIDODIARIO_DATABASE_URL`                      | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB` |
| `FILES_STORE`                                     | `STORAGE_BUCKET`                                                            |
| `AWS_ENDPOINT_URL`                                | `STORAGE_ENDPOINT`                                                          |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`      | `STORAGE_ACCESS_KEY`, `STORAGE_ACCESS_SECRET`                               |
| `AWS_REGION_NAME`                                 | `STORAGE_REGION`                                                            |

If you have a database dump, `make load-database` restores it into Postgres. The default file is `data/queridodiariodb.tar`; to use another one, run `make load-database DATABASE_RESTORE_FILE=path/to/dump.tar`.

### How do I run the pipelines?

| **Command**                                                  | **Pipeline**                                                                |
|--------------------------------------------------------------|-----------------------------------------------------------------------------|
| `make re-run`                                                | `gazette_texts`: text extraction, indexing and thematic indexes             |
| `make run`                                                   | `make setup` followed by `make re-run` (recreates the environment and deletes data) |
| `make aggregate-gazettes`                                    | `aggregates`: aggregates texts by municipality/state and year               |
| `docker compose run --rm app python main -p embedding_rerank` | `embedding_rerank`: recomputes the semantic score of excerpts left without one |

### How do I choose which gazettes to process?

With the `EXECUTION_MODE` variable in `envvars`:

- `ALL`: every gazette (the value in `config/sample.env`);
- `DAILY`: gazettes scraped in the last 24 hours (the code default when the variable is unset);
- `UNPROCESSED`: gazettes not yet marked as processed in the database.

In all three modes, `.zip` files are skipped and the most recent gazettes in the database are processed first.

### Where do I see the results?

- **OpenSearch**: the main `querido-diario` index and one index per theme (currently `ambiental` and `educacao`). To list them: `curl -u admin:admin "http://localhost:9200/_cat/indices?v"`.
- **Object storage**: a `.txt` next to each gazette file and, after `make aggregate-gazettes`, the compressed aggregates under `aggregates/<UF>/`.
- **Database**: the `processed` column of the `gazettes` table. Use `make sql` to open `psql` and `make shell` to open a shell in the application container.

More tips in the [end-to-end documentation](https://docs.queridodiario.ok.org.br/en/latest/contributing/end-to-end-configuration.html#environment-usage-tips).

### How do I add or change a theme?

Themes live in [`config/themes_config.json`](/config/themes_config.json). Each theme defines `name`, `index` (the OpenSearch index name), `queries`, `stopwords` and `entities`. The `gazette_texts` pipeline creates the theme index if it doesn't exist yet.

## Troubleshooting

The items from `cp: illegal option` through `relation "territories" does not exist`, plus the last one (`make retest`), were reproduced while setting up the environment with Docker Desktop on macOS (arm64). The others come from issues and the code. Several are worked around with a `docker-compose.override.yml` file in the repository root. `docker compose` reads that file automatically, so `docker-compose.yml` doesn't need to change. Don't commit it.

### `cp: illegal option -- -` and `env file .../envvars not found`

The `set-run-variable-values` target uses `cp --update=none`, an option of GNU `cp` that macOS `cp` doesn't have. The error is ignored (`|| true`), but `envvars` is not created and `docker compose` fails right after. Create the file manually and run the command again:

```console
cp -n config/sample.env envvars
make setup
```

### `401 UNAUTHORIZED` when pulling the MinIO image

In October 2026, the public MinIO images could no longer be pulled without authentication: pulling `quay.io/minio/minio:RELEASE.2025-09-07T16-13-09Z` (the one used in `docker-compose.yml`) fails with `401 UNAUTHORIZED`, and `minio/minio` on Docker Hub returns `pull access denied`. If you already have a MinIO image in your local Docker cache, or want to use another S3-compatible service, point to it in `docker-compose.override.yml`:

```yaml
services:
  minio:
    image: <s3-compatible-image-available-locally>
```

### The `queridodiariobucket` bucket doesn't exist

The official MinIO image doesn't create buckets from `MINIO_DEFAULT_BUCKETS`, and the `minio-createbucket` service is not started by `make setup`. Create the bucket with the `mc` client shipped in the server image:

```console
docker compose exec minio sh -c 'mc alias set local http://localhost:9000 minio-access-key minio-secret-key && mc mb --ignore-existing local/queridodiariobucket'
```

### `dependency failed to start: container ...-apache-tika-1 is unhealthy`

Targets that use `docker compose run app` (`make re-run`, `make retest`, `make shell`, etc.) wait for Tika to be healthy, but the healthcheck calls `curl`, which isn't installed in the Tika image. Also, the service `command` doesn't pass `--host 0.0.0.0`, so Tika only accepts connections from inside its own container. Fix both in `docker-compose.override.yml`:

```yaml
services:
  apache-tika:
    command: java -jar /tika-server.jar --host 0.0.0.0
    healthcheck:
      test: ["CMD", "bash", "-c", "echo > /dev/tcp/localhost/9998"]
```

Then recreate the service with `docker compose up -d apache-tika`.

### `Connection refused` to `localhost:9200`, `localhost:9998` or `127.0.0.1:9000`

`config/sample.env` points to `localhost`, which inside the `app` container is the container itself. Compose only overrides `POSTGRES_HOST`. To run the pipelines inside compose, use the service names in `envvars`:

```
STORAGE_ENDPOINT=http://minio:9000
OPENSEARCH_HOST=http://opensearch:9200
APACHE_TIKA_SERVER=http://apache-tika:9998
```

### `psycopg2.errors.UndefinedTable: relation "territories" does not exist`

The database is empty. Populate it with the scrapers or a dump (see [How do I feed the database and storage with gazettes?](#running)).

### The Tika build fails or the container shows `Invalid or corrupt jarfile /tika-server.jar`

This problem ([#73](https://github.com/okfn-brasil/querido-diario-data-processing/issues/73)) was fixed in [#123](https://github.com/okfn-brasil/querido-diario-data-processing/pull/123): the JAR is now downloaded from `archive.apache.org`, which keeps every version. Update your branch. To use another version, run `make build-tika-server TIKA_VERSION=x.y.z`.

### The process runs out of memory (OOM, `MemoryError`)

Large files can exhaust memory ([#25](https://github.com/okfn-brasil/querido-diario-data-processing/issues/25), [#6](https://github.com/okfn-brasil/querido-diario-data-processing/issues/6)). Settings available in `envvars`:

- `MEMORY_LIMIT_BYTES`: the pipeline caps its own address space (`RLIMIT_AS`) at 75% (soft) and 90% (hard) of this value, which defaults to 2 GB;
- `MAX_GAZETTE_FILE_SIZE_MB` (default `500`): larger files are skipped;
- `GAZETTE_QUERY_PAGE_SIZE` (default `1000`): how many gazettes are read from the database at a time;
- `TIKA_CHUNK_SIZE` (default `8192` bytes): size of the chunks sent to Tika.

For Tika's and OpenSearch's own memory, see the [monitoring guide](/docs/MONITORING_GUIDE.md) (Portuguese).

### `TransportError(413, '')` when indexing in OpenSearch

The document exceeds OpenSearch's maximum request size (`http.max_content_length`). The case is being investigated in [#112](https://github.com/okfn-brasil/querido-diario-data-processing/issues/112); the [monitoring guide](/docs/MONITORING_GUIDE.md#opensearch-lento-ou-falhando) shows how to raise the limit.

### `ChunkedEncodingError`, `IncompleteRead` or slow Tika requests

See the [monitoring guide](/docs/MONITORING_GUIDE.md#investigando-problemas-específicos). It explains how to find the problematic files in the logs. Retries are controlled by `TIKA_MAX_RETRIES` (default `5`) and `TIKA_RETRY_BASE_DELAY` (default `2.0` seconds).

### Association gazettes fail with a `KeyError` in `segmentation/factory.py`

Every gazette whose `territory_id` ends in `00000` is treated as an association gazette and needs a registered segmenter. Only the Alagoas one (`2700000`) exists today; the others are tracked in issues [#83 to #98](https://github.com/okfn-brasil/querido-diario-data-processing/issues?q=is%3Aissue+segmentador) ([#77](https://github.com/okfn-brasil/querido-diario-data-processing/issues/77)). See [How do I add an association segmenter?](#contributing).

### The extracted text has broken characters (e.g. `Ã©`)

Known issue, still open ([#76](https://github.com/okfn-brasil/querido-diario-data-processing/issues/76)).

### `make retest` shows dozens of errors

`make retest` runs every module in `tests/`, and some have known failures ([#57](https://github.com/okfn-brasil/querido-diario-data-processing/issues/57)): they expect services on `localhost` or use outdated mock and `opensearch-py` APIs. CI runs only the `tests/*_tests.py` files, with [`instrumented_test_runner.py`](/instrumented_test_runner.py). See [How do I run the tests?](#contributing).

## Contributing

### Where do I start?

Read Querido Diário's [Contribution Guide](https://docs.queridodiario.ok.org.br/en/latest/contributing/contribution-guide.html#contributing) and this repository's [CONTRIBUTING.md](/docs/CONTRIBUTING-en-US.md). Issues labeled [`good first issue`](https://github.com/okfn-brasil/querido-diario-data-processing/issues?q=is%3Aopen+label%3A%22good+first+issue%22) are a good starting point.

### How do I set up linting?

The project uses `pre-commit` with `ruff` (import sorting and formatting) and basic checks such as merge conflicts and private keys. See [`.pre-commit-config.yaml`](/.pre-commit-config.yaml).

```console
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
```

`requirements-dev.txt` includes `requirements.txt` (with `sentence-transformers`), so the install is heavy. CI runs `pre-commit run --all-files` on every PR to `main`.

### How do I run the tests?

CI ([`lint_and_unit.yaml`](/.github/workflows/lint_and_unit.yaml)) starts Postgres, OpenSearch, MinIO and Tika and runs:

```console
python instrumented_test_runner.py
```

That script runs only `tests/*_tests.py`. With the services up (`make setup`), run it inside compose:

```console
docker compose run --rm --no-deps app python instrumented_test_runner.py
```

The extraction tests in `tests/text_extraction_tests.py` expect Tika at `http://localhost:9998`, a port compose doesn't publish, so they fail in this mode. To run them too, use the Tika container's network (the container name depends on the project folder name). This way, all 41 tests passed:

```console
docker run --rm --network container:querido-diario-data-processing-apache-tika-1 \
  -v "$PWD":/mnt/code -w /mnt/code -e PYTHONPATH=/mnt/code \
  okfn-brasil/querido-diario-data-processing:latest python instrumented_test_runner.py
```

There are also per-module targets: `make retest-tika`, `make retest-tasks`, `make retest-main`, `make retest-index`, `make retest-postgres` and `make retest-digital-ocean-spaces`.

### How do I add an association segmenter?

1. Create a class in [`segmentation/segmenters/`](/segmentation/segmenters) that inherits from `AssociationSegmenter` ([`segmentation/base`](/segmentation/base)) and implements `get_gazette_segments`. Use [`al_associacao_municipios.py`](/segmentation/segmenters/al_associacao_municipios.py) as a reference.
2. Export the class in [`segmentation/segmenters/__init__.py`](/segmentation/segmenters/__init__.py).
3. Register the association's `territory_id` (ending in `00000`) in the `territory_to_segmenter_class` dictionary in [`segmentation/factory.py`](/segmentation/factory.py).

### What are the commit and PR conventions?

Commit messages follow the `type: description` format in Portuguese (`feat:`, `fix:`, `docs:`, `ci:`, etc.), as in the repository history. Every PR to `main` goes through CI lint and tests. A comment containing `cicd/build` on the PR triggers the image build workflows. Maintainers follow the [Guide for Maintainers](https://docs.queridodiario.ok.org.br/en/latest/contributing/contribution-guide.html#maintaining).

### Where do I ask for help?

On the [community Discord](https://go.ok.org.br/discord) (see [SUPPORT.md](/docs/SUPPORT-en-US.md)) or by opening an [issue](https://github.com/okfn-brasil/querido-diario-data-processing/issues).
