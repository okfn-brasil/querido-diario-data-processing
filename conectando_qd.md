## Configurando as credenciais para a comunicação dos dois projetos

Para configurar as credenciais é necessário mudar alguns parâmetros em **settings.py**. No repositório do [querido-diario]() na sua máquina vá até data_collection depois gazette e finalmente abra no seu editor de código o arquivo settings.py.

Mude os seguintes parâmetros:

~~~Python
###linha 21
FILES_STORE = config("FILES_STORE", default="data")

### Substitua por:
FILES_STORE = config("FILES_STORE", default="s3://queridodiariobucket/")

### linhas 44 a 46
QUERIDODIARIO_DATABASE_URL = config(
    "QUERIDODIARIO_DATABASE_URL", default="sqlite:///querido-diario.db"
)

### Substitua por:
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

Abra 2 terminais (1 com o repositório do [querido-diario-data-processing]() e outro com o [querido-diario](), ambos forked). Realize o **make setup** no repositório de processamento de dados e faça a busca scrapy crawl no repositório do querido-diario. Após isso, é possível...

Acesse os diários baixados através desse link: http://localhost:9000/minio/queridodiariobucket

## Configurando o ambiente do querido-diario

### Linux


### Windows

#### Usando WSL

Abra um novo terminal do Ubuntu e faça o clone do repositório forked do [querido-diario](https://github.com/okfn-brasil/querido-diario). Se tiver dúvidas, acesse o [tutorial de instalação do WSL no Windows](https://github.com/Luisa-Coelho/qd-data-processing/blob/readme_update/wsl_windows.md).

Para fazer a conexão você precisará ter baixado e instalado tudo que for necessário no repositório [querido-diario](https://github.com/okfn-brasil/querido-diario) em outro lugar na sua máquina WSL. Deixe as pastas próximas uma da outra para facilitar seu trabalho. Abra uma outra máquina Ubuntu para iniciar o repositório querido-diario.

Caso haja um erro com cython_sources, assim como na imagem:
![image](https://github.com/Luisa-Coelho/qd-data-processing/assets/87907716/57afdb93-26cd-4ddc-be43-53cd4fd60365)

Faça esse procedimento e instale os requirements-dev novamente:
~~~Linux
pip3 install wheel -v
pip3 install "cython<3.0.0" pyyaml==5.4.1 --no-build-isolation -v
~~~

Caso haja um erro com legacy-install
![image](https://github.com/Luisa-Coelho/qd-data-processing/assets/87907716/2040db6a-0d47-404f-aa98-2d2204a6ff4c)

Então faça o upgrade do pip e instale algumas bibliotecas essenciais do Linux:
~~~Linux
python3 -m pip install --upgrade pip
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
~~~

#### Usando o terminal do Windows

Lembre-se que para conectar o Banco de Dados é necessário vincular o terminal Windows com o Linux. Caso você não queira conectar é possível apenas fazer essas passos....

Caso haja um erro com "pinned with == "  na hora de instalar os requerimentos, utilize o pip3 install junto com o comando --no-deps, dessa forma:

~~~Linux
pip3 install -r data_collection/requirements-dev.txt --no-deps
~~~ 

Baixe o Visual Studio Comunidade [aqui](https://visualstudio.microsoft.com/pt-br/downloads/) . Seguindo os passos [aqui](https://github.com/okfn-brasil/querido-diario/blob/main/docs/CONTRIBUTING.md#em-linux), você deverá baixar o Visual Studio e baixar as configurações … 

Em **Componentes Individuais** selecione "SDK do Windows 10" ou '11 e Ferramentas de build do MSVC v143 - VS 2022 C++ x64/x86 (v14.32-17.4)". Ou conteúdo similares. Note que muitas vezes as versões Windows 10 SDK e MSVC v142 - VS 2019 C++ x64/x86 build tools serão atualizadas, portanto procure por itens similares em Componentes individuais para realizar a instalação (ou seja, mais novos)

Em **Cargas de Trabalho**, selecione “Desenvolvimento para desktop com C++”.

- **Mac**

...
