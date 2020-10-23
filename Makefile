IMAGE_NAMESPACE ?= serenata
IMAGE_NAME ?= querido-diario-data-processing
IMAGE_TAG ?= latest
POD_NAME ?= querido-diario-data-extraction

# Database info user to run the tests
DATABASE_CONTAINER_NAME ?= queridodiario-db
POSTGRES_PASSWORD ?= queridodiario
POSTGRES_USER ?= $(POSTGRES_PASSWORD)
POSTGRES_DB ?= $(POSTGRES_PASSWORD)
POSTGRES_HOST ?= localhost
POSTGRES_PORT ?= 5432

run-command=(podman run --rm -ti --volume $(PWD):/mnt/code:rw \
	--pod $(POD_NAME) \
	--env PYTHONPATH=/mnt/code \
	--env POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
	--env POSTGRES_USER=$(POSTGRES_USER) \
	--env POSTGRES_DB=$(POSTGRES_DB) \
	--env POSTGRES_HOST=$(POSTGRES_HOST) \
	--env POSTGRES_PORT=$(POSTGRES_PORT) \
	--user=$(UID):$(UID) $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) $1)

wait-for=(podman run --rm -ti --volume $(PWD):/mnt/code:rw \
	--pod $(POD_NAME) \
	--env PYTHONPATH=/mnt/code \
	--env POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
	--env POSTGRES_USER=$(POSTGRES_USER) \
	--env POSTGRES_DB=$(POSTGRES_DB) \
	--env POSTGRES_HOST=$(POSTGRES_HOST) \
	--env POSTGRES_PORT=$(POSTGRES_PORT) \
	--user=$(UID):$(UID) \
	$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) wait-for-it --timeout=30 $1)

.PHONY: black
black:
	podman run --rm -ti --volume $(PWD):/mnt/code:rw \
		--env PYTHONPATH=/mnt/code \
		--user=$(UID):$(UID) $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) \
		black .

.PHONY: build
build:
	podman build --tag $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) \
		-f Dockerfile $(PWD)

.PHONY: destroy
destroy:
	podman rmi --force $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG)

destroy-pod:
	podman pod rm --force --ignore $(POD_NAME)

create-pod: destroy-pod
	podman pod create --name $(POD_NAME)

.PHONY: test
test: create-pod database retest

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


shell:
	podman run --rm -ti --volume $(PWD):/mnt/code:rw \
	--env PYTHONPATH=/mnt/code \
	--user=$(UID):$(UID) $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) bash

.PHONY: coverage
coverage: create-pod database 
	$(call run-command, coverage erase)
	$(call run-command, coverage run -m unittest tests)
	$(call run-command, coverage report -m)

.PHONY: stop-database
stop-database:
	podman rm --force --ignore $(DATABASE_CONTAINER_NAME)

.PHONY: database
database: start-database wait-database

start-database:
	podman run -d --rm -ti \
		--name $(DATABASE_CONTAINER_NAME) \
		--pod $(POD_NAME) \
		-e POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
		-e POSTGRES_USER=$(POSTGRES_USER) \
		-e POSTGRES_DB=$(POSTGRES_DB) \
		postgres:12

wait-database:
	$(call wait-for, localhost:5432)

.PHONY: sql
sql:
	podman run --rm -ti \
		--pod $(POD_NAME) \
		postgres:12 psql -h localhost -U $(POSTGRES_USER)

.PHONY: run
run:
	podman run --rm -ti --volume $(PWD):/mnt/code:rw \
		--pod $(POD_NAME) \
		--env PYTHONPATH=/mnt/code \
		--env-file envvars \
		--user=$(UID):$(UID) $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) python main



