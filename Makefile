IMAGE_NAMESPACE ?= okfn-brasil
IMAGE_NAME ?= querido-diario-data-processing
IMAGE_TAG ?= latest
APACHE_TIKA_IMAGE_NAME ?=  querido-diario-apache-tika-server
APACHE_TIKA_IMAGE_TAG ?= latest
POD_NAME ?= querido-diario

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
DATABASE_RESTORE_FILE ?= contrib/data/queridodiariodb.tar
# OpenSearch port info
OPENSEARCH_PORT1 ?= 9200
OPENSEARCH_PORT2 ?= 9300
OPENSEARCH_CONTAINER_NAME ?= queridodiario-opensearch
APACHE_TIKA_CONTAINER_NAME ?= queridodiario-apache-tika-server
# Backend and API
FULL_PROJECT ?= false
API_PORT ?= 8080
BACKEND_PORT ?= 8000

run-command=(podman run --rm -ti --volume $(CURDIR):/mnt/code:rw \
	--pod $(POD_NAME) \
	--env PYTHONPATH=/mnt/code \
	--env POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
	--env POSTGRES_USER=$(POSTGRES_USER) \
	--env POSTGRES_DB=$(POSTGRES_DB) \
	--env POSTGRES_HOST=$(POSTGRES_HOST) \
	--env POSTGRES_PORT=$(POSTGRES_PORT) \
	$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) $1)

wait-for=(podman run --rm -ti --volume $(CURDIR):/mnt/code:rw \
	--pod $(POD_NAME) \
	--env PYTHONPATH=/mnt/code \
	--env POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
	--env POSTGRES_USER=$(POSTGRES_USER) \
	--env POSTGRES_DB=$(POSTGRES_DB) \
	--env POSTGRES_HOST=$(POSTGRES_HOST) \
	--env POSTGRES_PORT=$(POSTGRES_PORT) \
	$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) wait-for-it --timeout=60 $1)

.PHONY: black
black:
	podman run --rm -ti --volume $(CURDIR):/mnt/code:rw \
		--env PYTHONPATH=/mnt/code \
		$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) \
		black .

.PHONY: build-devel
build-devel:
	podman build --tag $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) \
		-f scripts/Dockerfile $(CURDIR)

.PHONY: build-tika-server
build-tika-server:
	podman build --tag $(IMAGE_NAMESPACE)/$(APACHE_TIKA_IMAGE_NAME):$(APACHE_TIKA_IMAGE_TAG) \
		-f scripts/Dockerfile_apache_tika $(CURDIR)

.PHONY: build
build: build-devel build-tika-server

.PHONY: login
login:
	podman login --username $(REGISTRY_USER) --password "$(REGISTRY_PASSWORD)" https://index.docker.io/v1/

.PHONY: publish
publish:
	podman tag $(IMAGE_NAMESPACE)/$(IMAGE_NAME):${IMAGE_TAG} $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(shell date --rfc-3339=date --utc)
	podman push $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(shell date --rfc-3339=date --utc)
	podman push $(IMAGE_NAMESPACE)/$(IMAGE_NAME):${IMAGE_TAG}

.PHONY: destroy
destroy:
	podman rmi --force $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG)

destroy-pod:
	podman pod rm --force --ignore $(POD_NAME)

create-pod: destroy-pod
ifeq ($(FULL_PROJECT), true)
	podman pod create -p $(POSTGRES_PORT):$(POSTGRES_PORT) \
				-p $(OPENSEARCH_PORT1):$(OPENSEARCH_PORT1) \
				-p $(STORAGE_PORT):$(STORAGE_PORT) \
				-p $(API_PORT):$(API_PORT) \
				-p $(BACKEND_PORT):$(BACKEND_PORT) \
				--name $(POD_NAME)
else
	podman pod create -p $(POSTGRES_PORT):$(POSTGRES_PORT) \
				-p $(OPENSEARCH_PORT1):$(OPENSEARCH_PORT1) \
				-p $(STORAGE_PORT):$(STORAGE_PORT) \
				--name $(POD_NAME)
endif

prepare-test-env: create-pod storage apache-tika-server opensearch database

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
	podman run -d --pod $(POD_NAME) --name $(APACHE_TIKA_CONTAINER_NAME) \
    	$(IMAGE_NAMESPACE)/$(APACHE_TIKA_IMAGE_NAME):$(APACHE_TIKA_IMAGE_TAG) \
		java -jar /tika-server.jar

stop-apache-tika-server:
	podman stop --ignore $(APACHE_TIKA_CONTAINER_NAME)
	podman rm --force --ignore $(APACHE_TIKA_CONTAINER_NAME)

.PHONY: apache-tika-server
apache-tika-server: stop-apache-tika-server start-apache-tika-server


shell: set-run-variable-values
	podman run --rm -ti --volume $(CURDIR):/mnt/code:rw \
		--pod $(POD_NAME) \
		--env PYTHONPATH=/mnt/code \
		--env-file envvars \
		$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) bash

.PHONY: coverage
coverage: prepare-test-env
	$(call run-command, coverage erase)
	$(call run-command, coverage run -m unittest tests)
	$(call run-command, coverage report -m)

.PHONY: stop-storage
stop-storage:
	podman rm --force --ignore $(STORAGE_CONTAINER_NAME)

.PHONY: storage
storage: stop-storage start-storage wait-storage

start-storage:
	podman run -d --rm -ti \
		--name $(STORAGE_CONTAINER_NAME) \
		--pod $(POD_NAME) \
		-e MINIO_ACCESS_KEY=$(STORAGE_ACCESS_KEY) \
		-e MINIO_SECRET_KEY=$(STORAGE_ACCESS_SECRET) \
		-e MINIO_DEFAULT_BUCKETS=$(STORAGE_BUCKET):public \
        $(STORAGE_IMAGE)

wait-storage:
	$(call wait-for, localhost:9000)

.PHONY: stop-database
stop-database:
	podman rm --force --ignore $(DATABASE_CONTAINER_NAME)

.PHONY: database
database: stop-database start-database wait-database

start-database:
	podman run -d --rm -ti \
		--name $(DATABASE_CONTAINER_NAME) \
		--pod $(POD_NAME) \
		-e POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
		-e POSTGRES_USER=$(POSTGRES_USER) \
		-e POSTGRES_DB=$(POSTGRES_DB) \
		$(POSTGRES_IMAGE)

wait-database:
	$(call wait-for, localhost:5432)

load-database: set-run-variable-values
ifneq ("$(wildcard $(DATABASE_RESTORE_FILE))","")
	podman cp $(DATABASE_RESTORE_FILE) $(DATABASE_CONTAINER_NAME):/mnt/dump_file
	podman exec $(DATABASE_CONTAINER_NAME) bash -c "pg_restore -v -c -h localhost -U $(POSTGRES_USER) -d $(POSTGRES_DB) /mnt/dump_file || true"
else
	@echo "cannot restore because file does not exists '$(DATABASE_RESTORE_FILE)'"
	@exit 1
endif

set-run-variable-values:
	cp --no-clobber contrib/sample.env envvars || true

.PHONY: sql
sql: set-run-variable-values
	podman run --rm -ti \
		--pod $(POD_NAME) \
		$(POSTGRES_IMAGE) psql -h localhost -U $(POSTGRES_USER) $(POSTGRES_DB)

.PHONY: setup
setup: set-run-variable-values create-pod storage apache-tika-server opensearch database

.PHONY: re-run
re-run: set-run-variable-values
	podman run --rm -ti --volume $(CURDIR):/mnt/code:rw \
		--pod $(POD_NAME) \
		--env PYTHONPATH=/mnt/code \
		--env-file envvars \
		$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) python main

.PHONY: run
run: setup re-run

.PHONY: shell-run
shell-run: set-run-variable-values
	podman run --rm -ti --volume $(CURDIR):/mnt/code:rw \
		--pod $(POD_NAME) \
		--env PYTHONPATH=/mnt/code \
		--env-file envvars \
		$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) bash

.PHONY: shell-database
shell-database: set-run-variable-values
	podman exec -it $(DATABASE_CONTAINER_NAME) \
	    psql -h localhost -d $(POSTGRES_DB) -U $(POSTGRES_USER)

opensearch: stop-opensearch start-opensearch wait-opensearch

start-opensearch:
	podman run -d --rm -ti \
		--name $(OPENSEARCH_CONTAINER_NAME) \
		--pod $(POD_NAME) \
		--env discovery.type=single-node \
		--env plugins.security.ssl.http.enabled=false \
		docker.io/opensearchproject/opensearch:2.9.0

stop-opensearch:
	podman rm --force --ignore $(OPENSEARCH_CONTAINER_NAME)

wait-opensearch:
	$(call wait-for, localhost:9200)

.PHONY: publish-tag
publish-tag:
	podman tag $(IMAGE_NAMESPACE)/$(IMAGE_NAME):${IMAGE_TAG} $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(shell git describe --tags)
	podman push $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(shell git describe --tags)

.PHONY: stop-aggregate-gazettes
stop-aggregate-gazettes:
	podman stop --ignore agg-gazettes
	podman rm --force --ignore agg-gazettes

.PHONY: aggregate-gazettes
aggregate-gazettes:  stop-aggregate-gazettes set-run-variable-values
	podman run -ti --volume $(CURDIR):/mnt/code:rw \
		--pod $(POD_NAME) \
		--env PYTHONPATH=/mnt/code \
		--env-file envvars \
		--name agg-gazettes \
		$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) python tasks/gazette_txt_to_xml.py