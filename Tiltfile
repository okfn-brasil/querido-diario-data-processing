load('ext://helm_resource', 'helm_resource', 'helm_repo')
load('ext://namespace', 'namespace_create')

update_settings(k8s_upsert_timeout_secs = 180)

tilt_settings_file = "./tilt-settings.yaml"
settings = read_yaml(tilt_settings_file)

github_user = settings.get("github_user")
if github_user == None or len(github_user) == 0:
	fail("Você deve informar o seu usuário do github no arquivo tilt-settings.yaml")

# helm repos
helm_repo('tika', 'https://apache.jfrog.io/artifactory/tika', 
	resource_name='helm-repo-tika', labels=['tika'])
helm_repo('bitnami', 'https://charts.bitnami.com/bitnami', 
	resource_name='helm-repo-bitnami', labels=['minio','postgresql'])
helm_repo('opensearch-operator', 
	'https://opensearch-project.github.io/opensearch-k8s-operator/', 
	resource_name='helm-repo-opensearch-operator', 
	labels=['opensearch'])

namespace_create('querido-diario')

# algumas das dependencias para rodar o pipeline 
helm_resource('tika', 
	'tika/tika', 
	namespace='tika', 
	flags=['--create-namespace', '--version=2.9.0'], 
	resource_deps=['helm-repo-tika'], 
	labels=['tika'])

helm_resource('postgresql',  
	'bitnami/postgresql',labels=['postgresql'], 
	namespace='postgresql', 
	flags=['--create-namespace', '--values=./scripts/postgresql-values.yaml', '--version=12.10.0'], 
	port_forwards=["5432"],
	resource_deps=['helm-repo-bitnami'])

# minio
helm_resource('minio',  
	'bitnami/minio', 
	namespace='minio', 
	flags=['--create-namespace', '--values=./scripts/minio-values.yaml', '--version=12.10.3'], 
	resource_deps=['helm-repo-bitnami'], 
	labels=['minio'], 
	port_forwards=['9000','9001'])

# Resource usado para baixar alguns diario e colocar eles no "S3" (minio) local
local_resource(
  "download-diarios",
  cmd="make diarios",
  labels=["makefile"],
  resource_deps=['minio']
)

# Colocar uma base de dados no postgresql para conseguir rodar o pipeline
local_resource(
  "download-base-de-dados",
  cmd="make base-de-dados",
  labels=["makefile"],
)

# opensearch
helm_resource('opensearch-operator',  
	'opensearch-operator/opensearch-operator', 
	namespace='opensearch-operator-system', 
	flags=['--create-namespace', '--version=2.4.0'], 
	resource_deps=['helm-repo-opensearch-operator'], 
	labels=['opensearch'])
k8s_yaml('./scripts/opensearch-cluster.yaml')
k8s_resource(new_name='opensearch', 
	objects=['querido-diario-opensearsch-cluster:OpenSearchCluster:querido-diario'],  
	labels=['opensearch'], 
	resource_deps=['opensearch-operator'])

# querido-diario pipeline
docker_build('ghcr.io/' + github_user + '/querido-diario-data-processing', '.', dockerfile='scripts/Dockerfile')

chart_values = read_yaml('./charts/querido-diario-pipeline/values.yaml')
pipeline_helm = helm('./charts/querido-diario-pipeline/', 
	name = "querido-diario",
	namespace = "querido-diario",
	set=["textExtractionJob.image.repository=ghcr.io/" + github_user + "/querido-diario-data-processing"])
k8s_yaml(pipeline_helm)

# container utilizado para ajustar a base de dados
postgresql_job_container_image = 'ghcr.io/' + github_user + '/querido-diario-data-processing-postgresql-client'

docker_build(postgresql_job_container_image, os.getcwd(), dockerfile='scripts/postgresql-client.dockerfile')

postgresql_values = read_yaml('./scripts/postgresql-values.yaml') 
diarios ='1302603/2023-08-16/eb5522a3e160ba9129bd05617a68badd4e8ee381.pdf,3304557/2023-08-17/00e276910596fa4b4b7eb9cbec8a221e79ebbe0e,4205407/2023-08-10/c6eb1ce23b9bea9c3a72aece0e762eb883a8a00a.pdf,4106902/2023-08-14/b416ef3008654f84e2bee57f89cfd0513f8ec800,2611606/2023-08-12/7b010f0485bbb3bf18500a6ce90346916e776d62.pdf'

base_de_dados_job = read_yaml('./scripts/postgresql-base-criacao.yml') 
base_de_dados_job["spec"]["template"]["spec"]["containers"][0]["image"] = postgresql_job_container_image
for envVar in base_de_dados_job["spec"]["template"]["spec"]["containers"][0]["env"]:
	if envVar.get("name") == "PGPASSWORD":
		envVar["value"] = postgresql_values["global"]["postgresql"]["auth"]["password"]
	if envVar.get("name") == "PGUSER":
		envVar["value"] = postgresql_values["global"]["postgresql"]["auth"]["username"]
	if envVar.get("name") == "PGDATABASE":
		envVar["value"] = postgresql_values["global"]["postgresql"]["auth"]["database"]
	if envVar.get("name") == "PGHOST":
		envVar["value"] = chart_values["postgresql"]["host"]
	if envVar.get("name") == "PGPORT":
		envVar["value"] = str(chart_values["postgresql"]["port"])
	if envVar.get("name") == "DIARIOS":
		envVar["value"] = diarios
k8s_yaml(encode_yaml(base_de_dados_job))
k8s_resource(workload='cria-base-de-dados', labels=['postgresql'], resource_deps=['postgresql'])

minio_job_container_image = 'ghcr.io/' + github_user + '/querido-diario-data-processing-minio-client'
minio_values = read_yaml('./scripts/minio-values.yaml') 
docker_build(minio_job_container_image, os.getcwd(), dockerfile='scripts/minio-client.dockerfile')

minio_job = read_yaml('./scripts/diarios-upload-job.yaml') 
minio_job["spec"]["template"]["spec"]["containers"][0]["image"] = minio_job_container_image
for envVar in minio_job["spec"]["template"]["spec"]["containers"][0]["env"]:
	if envVar.get("name") == "MINIO_ACCESS_KEY":
		envVar["value"] = minio_values["provisioning"]["users"][0]["username"]
	if envVar.get("name") == "MINIO_SECRET_KEY":
		envVar["value"] = minio_values["provisioning"]["users"][0]["password"]
	if envVar.get("name") == "MINIO_ACCESS_BUCKET":
		envVar["value"] = chart_values["storage"]["bucket"]
	if envVar.get("name") == "MINIO_ACCESS_URL":
		envVar["value"] = chart_values["storage"]["endpoint"]


k8s_yaml(encode_yaml(minio_job))
k8s_resource(workload='diarios-upload-job', labels=['minio'],  resource_deps=['minio'])




