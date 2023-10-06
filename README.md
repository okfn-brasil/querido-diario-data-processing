# querido-diario-data-processing

## Setup

- [Install podman](https://podman.io/getting-started/installation)
- execute build stage (only the first time):
```console
make build
```
- execute setup stage:
```console
make setup
```

-----------------------------
- [x]  como configurar as credenciais em ambos os projetos para que eles se comuniquem
- [ ]  como realizar um seed no data-processing usando um spider do querido-diario

Para configurar as credenciais é necessário mudar alguns parâmetros em settings.py. No repositório do [querido-diario]() na sua máquina vá até data_collection depois gazette e finalmente abra no seu editor de código o arquivo settings.py.

Mude os seguintes parâmetros:

~~~Python
###linha xxx
FILES_STORE = config("FILES_STORE", default="s3://queridodiariobucket/")

### linha xx
QUERIDODIARIO_DATABASE_URL = config( "QUERIDODIARIO_DATABASE_URL", default="postgresql://queridodiario:queridodiario@127.0.0.1:5432/queridodiariodb" )

### linhas 52 a 56
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_ENDPOINT_URL = config("AWS_ENDPOINT_URL", default="")
AWS_REGION_NAME = config("AWS_REGION_NAME", default="")
FILES_STORE_S3_ACL = config("FILES_STORE_S3_ACL", default="public-read")

# Substitua por
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="minio-access-key")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="minio-secret-key")
AWS_ENDPOINT_URL = config("AWS_ENDPOINT_URL", default="http://localhost:9000/")
AWS_REGION_NAME = config("AWS_REGION_NAME", default="us-east-1")
FILES_STORE_S3_ACL = config("FILES_STORE_S3_ACL", default="public-read")
~~~


- **Linux**


- **Windows**

1. **Usando WSL**
Abra um novo terminal do Ubuntu e faça o clone do repositório forked do [querido-diario](). 

Para fazer a conexão você precisará ter baixado e instalado tudo que for necessário no repositório [querido-diario]() em outro lugar na sua máquina WSL. Deixe as pastas próximas uma da outra para facilitar seu trabalho. Abra uma outra máquina Ubuntu para iniciar o repositório querido-diario.

Caso haja um erro com cython_sources, assim como na imagem:

![[Pasted image 20231005102449.png]]

Faça esse procedimento e instale os requirements-dev novamente:

~~~Linux
pip3 install wheel -v
pip3 install "cython<3.0.0" pyyaml==5.4.1 --no-build-isolation -v
~~~

Caso haja um erro com legacy-install
![[Pasted image 20231005104343.png]]
![[Pasted image 20231005103545.png]]

Então faça o upgrade do pip e instale algumas bibliotecas essenciais do Linux:

~~~Linux
python3 -m pip install --upgrade pip
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
~~~

2. **Usando o terminal do Windows**

Lembre-se que para conectar o Banco de Dados é necessário vincular o terminal Windows com o Linux. Caso você não queira conectar é possível apenas fazer essas passos....

Caso haja um erro com "pinned with == "  na hora de instalar os requerimentos, utilize o pip3 install e adicione um dos comandos abaixo:

~~~Linux
pip install -r data_collection/requirements-dev.txt --no-deps
~~~ 

Baixe o Visual Studio Comunidade [aqui](https://visualstudio.microsoft.com/pt-br/downloads/) . Seguindo os passos [aqui](https://github.com/okfn-brasil/querido-diario/blob/main/docs/CONTRIBUTING.md#em-linux), você deverá baixar o Visual Studio e baixar as configurações … 

Em **Componentes Individuais** selecione "SDK do Windows 10" ou '11 e Ferramentas de build do MSVC v143 - VS 2022 C++ x64/x86 (v14.32-17.4)". Ou conteúdo similares. Note que muitas vezes as versões Windows 10 SDK e MSVC v142 - VS 2019 C++ x64/x86 build tools serão atualizadas, portanto procure por itens similares em Componentes individuais para realizar a instalação (ou seja, mais novos)

Em **Cargas de Trabalho**, selecione “Desenvolvimento para desktop com C++”.

- **Mac**

...
## Populate data
Populate data [following this instructions](https://github.com/okfn-brasil/querido-diario#run-inside-a-container).

- you can see created data inside [storage](http://localhost:9000/minio/queridodiariobucket) using [local credentials](contrib/sample.env#L3)
- you can see gazettes not processed yet connecting on database
- open database console in a new terminal
```console
make shell-database
```
- and run a query to see gazettes not processed
```sql
select processed, count(1) from gazettes g group by processed;
```

## Run
- execute processing stage:
```console
make re-run
```
- and see gazettes processed running the query above
- you can search using ElasticSearch
```console
curl 'http://localhost:9200/querido-diario/_search' \
  -H 'Content-Type: application/json' \
  --data-raw '{"query":{"query_string":{"query":"*"}},"size":2}'
```
