
IMAGE_NAMESPACE ?= okfn-brasil
IMAGE_NAME ?= querido-diario-data-processing
IMAGE_TAG ?= latest
CLUSTER_NAME ?= querido-diario
CLUSTER_NODES_COUNT ?= 3
FILES_DIR ?= files
DIARIOS_DIR ?= $(FILES_DIR)/diarios
QUERIDO_DIARIO_CDN ?= https://querido-diario.nyc3.cdn.digitaloceanspaces.com/
QUERIDO_DIARIO_BASEDADOS ?= https://querido-diario-misc.nyc3.cdn.digitaloceanspaces.com/queridodiario_dump.zip
REGISTRY_NAME ?= querido-diario-registry

k8s=kubectl --context $(CLUSTER_NAME) $(1)

start-cluster:
	ctlptl create cluster minikube --registry=querido-diario-registry --name "$(CLUSTER_NAME)" --minikube-start-flags "--nodes=$(CLUSTER_NODES_COUNT)" --minikube-container-runtime "docker"

delete-cluster:
	ctlptl delete cluster $(CLUSTER_NAME) --cascade "true" --ignore-not-found

.PHONY: cluster
cluster: delete-cluster start-cluster

DIARIOS := 1302603/2023-08-16/eb5522a3e160ba9129bd05617a68badd4e8ee381.pdf 3304557/2023-08-17/00e276910596fa4b4b7eb9cbec8a221e79ebbe0e 4205407/2023-08-10/c6eb1ce23b9bea9c3a72aece0e762eb883a8a00a.pdf 4106902/2023-08-14/b416ef3008654f84e2bee57f89cfd0513f8ec800 2611606/2023-08-12/7b010f0485bbb3bf18500a6ce90346916e776d62.pdf
$(DIARIOS):
	@if [ ! -f $(join $(DIARIOS_DIR),/$@) ]; then \
		echo "Baixando $@"; \
		curl -XGET --output-dir $(DIARIOS_DIR) --create-dirs --output $@ $(QUERIDO_DIARIO_CDN)$@; \
	fi

# Colocar alguns diarios no s3 rodando no cluster local
.PHONY: diarios
diarios: $(DIARIOS)


$(FILES_DIR)/queridodiario_dump.zip:
	curl -XGET --output-dir $(FILES_DIR) --create-dirs --output queridodiario_dump.zip https://querido-diario-misc.nyc3.cdn.digitaloceanspaces.com/queridodiario_dump.zip

$(FILES_DIR)/queridodiario_dump.sql:
	unzip -u $(FILES_DIR)/queridodiario_dump.zip -d $(FILES_DIR)

.PHONY: base-de-dados
base-de-dados: $(FILES_DIR)/queridodiario_dump.zip $(FILES_DIR)/queridodiario_dump.sql
