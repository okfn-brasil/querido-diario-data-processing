IMAGE_NAMESPACE ?= ghcr.io/okfn-brasil
IMAGE_NAME ?= querido-diario-data-processing
IMAGE_TAG ?= latest
APACHE_TIKA_IMAGE_NAME ?=  querido-diario-apache-tika-server
APACHE_TIKA_IMAGE_TAG ?= latest
CLUSTER_NAME ?= "querido-diario" 
CLUSTER_NODES_COUNT ?= 5
SCRIPT_DIR ?= $(PWD)/scripts
BUCKET_NAME ?= queridodiariobucket 
FILES_DIR ?= files
DIARIOS_DIR ?= $(FILES_DIR)/diarios
DATABASE_DUMP ?= $(FILES_DIR)/queridodiario_dump.sql

QUERIDO_DIARIO_CDN ?= https://querido-diario.nyc3.cdn.digitaloceanspaces.com/

helm=helm --kube-context $(CLUSTER_NAME) $(1)
helm_install=$(helm) upgrade --install --create-namespace --devel --wait
k8s=kubectl --context $(CLUSTER_NAME) $(1)

.PHONY: build-pipeline-image
build-pipeline-image:
	podman build --tag $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG) \
		--ignorefile .gitignore \
        	-f scripts/Dockerfile $(PWD)
	- rm $(FILES_DIR)/$(IMAGE_NAME)-$(IMAGE_TAG).tar

$(FILES_DIR)/$(IMAGE_NAME)-$(IMAGE_TAG).tar:
	podman save -o $(FILES_DIR)/$(IMAGE_NAME)-$(IMAGE_TAG).tar $(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: carrega-images 
carrega-images: $(FILES_DIR)/$(IMAGE_NAME)-$(IMAGE_TAG).tar
	minikube --profile $(CLUSTER_NAME) image load --overwrite=true -v=2 --alsologtostderr $(FILES_DIR)/$(IMAGE_NAME)-$(IMAGE_TAG).tar

uninstall-tika:
	- $(helm) uninstall tika

install-tika: 
	$(helm_install) --namespace tika tika tika/tika

.PHONY: tika
tika:   uninstall-tika install-tika

.PHONY: postgresql
postgresql:
	$(helm_install) --namespace postgresql --values $(SCRIPT_DIR)/postgresql-values.yaml --version 12.10.0 postgresql bitnami/postgresql 

.PHONY: uninstall-postgresql
uninstall-postgresql:
	- $(helm) uninstall --wait --namespace postgresql postgresql

.PHONY: uninstall-minio
uninstall-minio:
	- $(helm) uninstall --wait --namespace minio minio

.PHONY: minio
minio:  uninstall-minio
	$(helm_install) --namespace minio --values $(SCRIPT_DIR)/minio-values.yaml --version 12.8.15 minio bitnami/minio 

uninstall-opensearch: 
	- $(k8s) delete --wait --ignore-not-found -f $(SCRIPT_DIR)/opensearch-cluster.yaml
	- $(helm) uninstall -n opensearch-operator opensearch-operator 

install-opensearch: 
	$(helm_install) -n opensearch-operator opensearch-operator opensearch-operator/opensearch-operator
	$(k8s) wait --for=condition="Ready" pods -n opensearch-operator --all
	$(k8s) apply -f $(SCRIPT_DIR)/opensearch-cluster.yaml

.PHONY: opensearch
opensearch: uninstall-opensearch install-opensearch

.PHONY: delete-cluster
delete-cluster:
	minikube delete --profile $(CLUSTER_NAME)

start-cluster:
	minikube start --driver=kvm2 --cpus 6 --memory 6gb --disk-size 40g \
		--nodes $(CLUSTER_NODES_COUNT)  --profile $(CLUSTER_NAME)
	# O CSI default do minikube nao funciona legal com multiplos nos. 
	# Então vamos usar um diferente.
	minikube --profile $(CLUSTER_NAME) addons disable storage-provisioner
	minikube --profile $(CLUSTER_NAME) addons disable default-storageclass
	minikube --profile $(CLUSTER_NAME) addons enable volumesnapshots
	minikube --profile $(CLUSTER_NAME) addons enable csi-hostpath-driver
	kubectl --context $(CLUSTER_NAME) patch storageclass csi-hostpath-sc -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

.PHONY: cluster
cluster: delete-cluster start-cluster

.PHONY: helm-repo
helm-repo:
	helm repo add bitnami https://charts.bitnami.com/bitnami
	helm repo add tika https://apache.jfrog.io/artifactory/tika
	helm repo add opensearch https://opensearch-project.github.io/helm-charts/
	helm repo add opensearch-operator https://opster.github.io/opensearch-k8s-operator/
	helm repo add minio https://helm.min.io/
	helm repo update

.PHONY: setup
setup: cluster reinstall-stack 

.PHONY: reinstall-stack
reinstall-stack: helm-repo tika minio postgresql opensearch
	$(k8s) wait --for=condition="Ready" pods -A --all -l job-name!=minio-provisioning

.PHONY: install-pipeline
install-pipeline: 
	$(helm_install) \
		--set opensearch.user=$(shell $(k8s) get secret querido-diario-index-admin-password -n default -o jsonpath="{.data.username}" | base64 -d) \
		--set opensearch.password=$(shell $(k8s) get secret querido-diario-index-admin-password -n default -o jsonpath="{.data.password}" | base64 -d) \
		--set textExtractionJob.image="$(IMAGE_NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG)" \
		querido-diario-pipeline charts/querido-diario-pipeline/

.PHONY: uninstall-pipeline
uninstall-pipeline: 
	- $(helm) uninstall querido-diario-pipeline

.PHONY: credenciais
credenciais: 
	@echo "Essas são as credenciais para você acessar os serviços rodando no cluster local:"
	@echo POSTGRES_PASSWORD = $(shell kubectl get secret --namespace postgresql postgresql -o jsonpath="{.data.password}" | base64 -d)
	@echo POSTGRES_ADMIN_PASSWORD=$(shell kubectl get secret --namespace postgresql postgresql -o jsonpath="{.data.postgres-password}" | base64 -d)
	@echo MINIO_ROOT_USER=$(shell $(k8s) get secret --namespace minio minio -o jsonpath="{.data.root-user}" | base64 -d)
	@echo MINIO_ROOT_PASSWORD=$(shell $(k8s) get secret --namespace minio minio -o jsonpath="{.data.root-password}" | base64 -d)
	@echo OPENSEARCH_USER=$(shell $(k8s) get secret querido-diario-index-admin-password -n default -o jsonpath="{.data.username}" | base64 -d)
	@echo OPENSEARCH_PASSWORD=$(shell $(k8s) get secret querido-diario-index-admin-password -n default -o jsonpath="{.data.password}" | base64 -d)

DIARIOS := 1302603/2023-08-16/eb5522a3e160ba9129bd05617a68badd4e8ee381.pdf 3304557/2023-08-17/00e276910596fa4b4b7eb9cbec8a221e79ebbe0e 4205407/2023-08-10/c6eb1ce23b9bea9c3a72aece0e762eb883a8a00a.pdf 4106902/2023-08-14/b416ef3008654f84e2bee57f89cfd0513f8ec800 2611606/2023-08-12/7b010f0485bbb3bf18500a6ce90346916e776d62.pdf
$(DIARIOS):
	@if [ ! -f $(join $(DIARIOS_DIR),/$@) ]; then \
		echo "Baixando $@"; \
		curl -XGET --output-dir $(DIARIOS_DIR) --create-dirs --output $@ $(QUERIDO_DIARIO_CDN)$@; \
	fi 
	
.PHONY: prepara-ambiente
prepara-ambiente: expoe-servicos diarios base-de-dados derruba-servicos

.PHONY: expoe-servicos
expoe-servicos: derruba-servicos
	@nohup $(k8s) port-forward --namespace minio svc/minio 9000:9000 > /dev/null 2>&1 &
	@nohup $(k8s) port-forward --namespace minio svc/minio 9001:9001 > /dev/null 2>&1 &
	@nohup $(k8s) port-forward --namespace postgresql svc/postgresql 5432:5432 > /dev/null 2>&1 &
	@echo "Minio esta disponivel na porta 9000 e 9001"
	@echo "Postgresql está disponivel na porta 5432"
	@echo "Para remover o mapeamento das portas execute: make derruba-servicoes"

.PHONY: derruba-servicos
derruba-servicos:
	- pkill -f "svc/minio 9000"
	- pkill -f "svc/minio 9001"
	- pkill -f "svc/postgresql 5432"

# Colocar alguns diarios no s3 rodando no cluster local
.PHONY: diarios
diarios: $(DIARIOS)
	- s3cmd --no-ssl --no-encrypt \
		--access_key=querido-diario-user \
		--secret_key=querido-diario-secret \
		--host 127.0.0.1:9000 \
		--host-bucket "s3.us-east-1.127.0.0.1:9000" \
		--bucket-location=us-east-1 \
		sync files/diarios/* s3://queridodiariobucket

$(DATABASE_DUMP):
	curl -XGET --output-dir $(FILES_DIR) --create-dirs  --output queridodiario_dump.zip \
		https://querido-diario-misc.nyc3.cdn.digitaloceanspaces.com/queridodiario_dump.zip 
	unzip $(FILES_DIR)/queridodiario_dump.zip -d $(FILES_DIR)

# Configura a base de dados com alguns diarios para serem processados. 
.PHONY: base-de-dados
base-de-dados: $(DATABASE_DUMP)
	PGPASSWORD="$(shell $(k8s) get secret --namespace postgresql postgresql -o jsonpath="{.data.password}" | base64 -d)" \
		   psql --host 127.0.0.1 -U queridodiario -d queridodiariodb -p 5432 -f  $(DATABASE_DUMP)
	$(k8s) delete pod --namespace postgresql --wait --ignore-not-found postgresql-client
	$(k8s) run postgresql-client --rm --tty -i --restart='Never' \
		--namespace postgresql \
		--image docker.io/bitnami/postgresql:15.4.0-debian-11-r10 \
		--env="PGPASSWORD=$(shell $(k8s) get secret --namespace postgresql postgresql -o jsonpath="{.data.password}" | base64 -d)"  \
		--command -- psql --host postgresql -U queridodiario -d queridodiariodb -p 5432 --command "update gazettes set processed=true,scraped_at = CURRENT_TIMESTAMP;"
	@for diario in $(DIARIOS); do \
		$(k8s) run postgresql-client --rm --tty -i --restart='Never' \
			--namespace postgresql \
			--image docker.io/bitnami/postgresql:15.4.0-debian-11-r10 \
			--env="PGPASSWORD=$(shell $(k8s) get secret --namespace postgresql postgresql -o jsonpath="{.data.password}" | base64 -d)"  \
			--command -- psql --host postgresql -U queridodiario -d queridodiariodb -p 5432 --command "update gazettes set processed=false where file_path = '$$diario';"; \
	done

.PHONY: shell-database
shell-database:
	$(k8s) run postgresql-client --rm --tty -i --restart='Never' \
		--namespace postgresql \
		--image docker.io/bitnami/postgresql:15.4.0-debian-11-r10 \
		--env="PGPASSWORD=$(shell $(k8s) get secret --namespace postgresql postgresql -o jsonpath="{.data.password}" | base64 -d)"  \
		--command -- psql --host postgresql -U queridodiario -d queridodiariodb -p 5432
