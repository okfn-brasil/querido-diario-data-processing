IMAGE_NAMESPACE ?= okfn-brasil
IMAGE_NAME ?= querido-diario-data-processing
IMAGE_TAG ?= latest
APACHE_TIKA_IMAGE_NAME ?=  querido-diario-apache-tika-server
APACHE_TIKA_IMAGE_TAG ?= latest
POD_NAME ?= querido-diario

# Architecture detection and configuration
CURRENT_ARCH := $(shell uname -m)
ifeq ($(CURRENT_ARCH),x86_64)
    DEFAULT_PLATFORM := linux/amd64
else ifeq ($(CURRENT_ARCH),aarch64)
    DEFAULT_PLATFORM := linux/arm64
else ifeq ($(CURRENT_ARCH),arm64)
    DEFAULT_PLATFORM := linux/arm64
else
    DEFAULT_PLATFORM := linux/amd64
endif

# Allow override via command line flags
ifdef amd64
    PLATFORM := linux/amd64
else ifdef arm64
    PLATFORM := linux/arm64
else
    PLATFORM := $(DEFAULT_PLATFORM)
endif

# S3 mock
STORAGE_BUCKET ?= queridodiariobucket
STORAGE_IMAGE ?= docker.io/bitnami/minio:2021.4.6
STORAGE_CONTAINER_NAME ?= queridodiario-storage
STORAGE_ACCESS_KEY ?= minio-access-key
STORAGE_ACCESS_SECRET ?= minio-secret-key
STORAGE_PORT ?= 9000
# Database info user to run the tests
DATABASE_CONTAINER_NAME ?= queridodiario-db
POSTGRES_PASSWORD ?= queridodiario
POSTGRES_USER ?= $(POSTGRES_PASSWORD)
POSTGRES_DB ?= queridodiariodb
POSTGRES_HOST ?= localhost
POSTGRES_PORT ?= 5432
POSTGRES_IMAGE ?= docker.io/postgres:11
DATABASE_RESTORE_FILE ?= data/queridodiariodb.tar
# OpenSearch port info
OPENSEARCH_PORT1 ?= 9200
OPENSEARCH_PORT2 ?= 9300
OPENSEARCH_CONTAINER_NAME ?= queridodiario-opensearch
APACHE_TIKA_CONTAINER_NAME ?= queridodiario-apache-tika-server
# Backend and API
FULL_PROJECT ?= false
API_PORT ?= 8080
BACKEND_PORT ?= 8000

run-command=docker compose run --attach --rm app $1

wait-for=docker compose run --rm app wait-for-it --timeout=60 $1

.PHONY: black
black:
	$(call run-command, black .)

.PHONY: build-devel
build-devel:
	docker build --platform $(PLATFORM) --tag $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) \
		-f Dockerfile $(CURDIR)

.PHONY: build-tika-server
build-tika-server:
	docker build --platform $(PLATFORM) --tag $(IMAGE_NAMESPACE)/$(APACHE_TIKA_IMAGE_NAME):$(APACHE_TIKA_IMAGE_TAG) \
		-f Dockerfile_apache_tika $(CURDIR)

.PHONY: build-multi-arch
build-multi-arch:
	docker buildx build --platform linux/amd64,linux/arm64 --tag $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) \
		-f Dockerfile $(CURDIR)
	docker buildx build --platform linux/amd64,linux/arm64 --tag $(IMAGE_NAMESPACE)/$(APACHE_TIKA_IMAGE_NAME):$(APACHE_TIKA_IMAGE_TAG) \
		-f Dockerfile_apache_tika $(CURDIR)

.PHONY: build
build: build-devel build-tika-server

.PHONY: login
login:
	docker login --username $(REGISTRY_USER) --password "$(REGISTRY_PASSWORD)" https://index.docker.io/v1/

.PHONY: publish
publish:
	docker tag $(IMAGE_NAMESPACE)/$(IMAGE_NAME):${IMAGE_TAG} $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(shell date --rfc-3339=date --utc)
	docker push $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(shell date --rfc-3339=date --utc)
	docker push $(IMAGE_NAMESPACE)/$(IMAGE_NAME):${IMAGE_TAG}

.PHONY: destroy
destroy:
	docker rmi --force $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG)

destroy-services: set-run-variable-values
	docker compose down --volumes --remove-orphans

create-services: destroy-services
	docker compose up -d postgres opensearch minio apache-tika

prepare-test-env: create-services

.PHONY: test
test: prepare-test-env retest

.PHONY: retest
retest:
	$(call run-command, python -m unittest -f tests)

.PHONY: retest-digital-ocean-spaces
retest-digital-ocean-spaces:
	$(call run-command, python -m unittest -f tests/digital_ocean_spaces.py)

.PHONY: retest-postgres
retest-postgres:
	$(call run-command, python -m unittest -f tests/postgresql.py)

.PHONY: retest-tasks
retest-tasks:
	$(call run-command, python -m unittest -f tests/text_extraction_task_tests.py)

.PHONY: retest-main
retest-main:
	$(call run-command, python -m unittest -f tests/main_tests.py)

.PHONY: retest-index
retest-index:
	$(call run-command, python -m unittest -f tests/opensearch.py)

.PHONY: retest-tika
retest-tika:
	$(call run-command, python -m unittest -f tests/text_extraction_tests.py)

start-apache-tika-server:
	docker compose up -d apache-tika

stop-apache-tika-server:
	docker compose stop apache-tika

.PHONY: apache-tika-server
apache-tika-server: stop-apache-tika-server start-apache-tika-server


shell: set-run-variable-values
	$(call run-command, bash)

.PHONY: coverage
coverage: prepare-test-env
	$(call run-command, coverage erase)
	$(call run-command, coverage run -m unittest tests)
	$(call run-command, coverage report -m)

.PHONY: stop-storage
stop-storage:
	docker compose stop minio

.PHONY: storage
storage: stop-storage start-storage wait-storage

start-storage:
	docker compose up -d minio

wait-storage:
	$(call wait-for, minio:9000)

.PHONY: stop-database
stop-database:
	docker compose stop postgres

.PHONY: database
database: stop-database start-database wait-database

start-database:
	docker compose up -d postgres

wait-database:
	$(call wait-for, postgres:5432)

load-database: set-run-variable-values
ifneq ("$(wildcard $(DATABASE_RESTORE_FILE))","")
	docker compose cp $(DATABASE_RESTORE_FILE) postgres:/mnt/dump_file
	docker compose exec postgres bash -c "pg_restore -v -c -h localhost -U $(POSTGRES_USER) -d $(POSTGRES_DB) /mnt/dump_file || true"
else
	@echo "cannot restore because file does not exists '$(DATABASE_RESTORE_FILE)'"
	@exit 1
endif

set-run-variable-values:
	cp --no-clobber config/sample.env envvars || true

.PHONY: sql
sql: set-run-variable-values
	docker compose exec postgres psql -h localhost -U $(POSTGRES_USER) $(POSTGRES_DB)

.PHONY: setup
setup: set-run-variable-values create-services

.PHONY: re-run
re-run: set-run-variable-values
	$(call run-command, python main)

.PHONY: run
run: setup re-run

.PHONY: shell-run
shell-run: set-run-variable-values
	$(call run-command, bash)

.PHONY: shell-database
shell-database: set-run-variable-values
	docker compose exec postgres psql -h localhost -d $(POSTGRES_DB) -U $(POSTGRES_USER)

opensearch: stop-opensearch start-opensearch wait-opensearch

start-opensearch:
	docker compose up -d opensearch

stop-opensearch:
	docker compose stop opensearch

wait-opensearch:
	$(call wait-for, opensearch:9200)

.PHONY: publish-tag
publish-tag:
	docker tag $(IMAGE_NAMESPACE)/$(IMAGE_NAME):${IMAGE_TAG} $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(shell git describe --tags)
	docker push $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(shell git describe --tags)

.PHONY: aggregate-gazettes
aggregate-gazettes: set-run-variable-values
	$(call run-command, python main -p aggregates)

.PHONY: help-arch
help-arch:
	@echo "Architecture build options:"
	@echo "  make build                - Build for current architecture ($(DEFAULT_PLATFORM))"
	@echo "  make build amd64=1        - Build for AMD64 architecture"
	@echo "  make build arm64=1        - Build for ARM64 architecture"
	@echo "  make build-multi-arch     - Build for both amd64 and arm64 architectures"
	@echo ""
	@echo "Current system architecture: $(CURRENT_ARCH) -> $(DEFAULT_PLATFORM)"
