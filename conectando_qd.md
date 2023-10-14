PT/BR [Tutorial geral](https://github.com/Luisa-Coelho/qd-data-processing/blob/readme_update/tutorial.md) | [Configurando os diferentes ambientes](https://github.com/Luisa-Coelho/qd-data-processing/blob/readme_update/configurando_ambientes.md) | [Conectando ao querido-diario](https://github.com/Luisa-Coelho/qd-data-processing/blob/readme_update/conectando_qd.md)

EN/US

## Configurando as credenciais para a comunicação dos dois projetos

Para configurar as credenciais é necessário vincular os dois projetos como um só. Para isso é necessário **criar um arquivo .env** na raíz do repositório [querido-diario]() e inserir parâmetros coincidentes com o processamento do repositório [queridod-diario-data-processing](). Depois de ter realizado o fork do querido-diario, abra este repositório na sua máquina e insira um arquivo .env com as seguintes informações.

~~~.env
AWS_ACCESS_KEY_ID=minio-access-key
AWS_SECRET_ACCESS_KEY=minio-secret-key
AWS_ENDPOINT_URL=http://127.0.0.1:9000/
AWS_REGION_NAME=us-east-1
FILES_STORE=s3://queridodiariobucket/
FILES_STORE_S3_ACL=public-read
QUERIDODIARIO_DATABASE_URL=postgresql+psycopg2://queridodiario:queridodiario@127.0.0.1:5432/queridodiariodb
~~~

A variável .env já está como ignorada no projeto do querido-diario, portanto não é necessário mudar mais nada. Para executar a requisição abra 2 terminais (1 com o repositório do [querido-diario-data-processing]() e outro com o [querido-diario](), ambos forked). Realize o **make setup** no repositório de processamento de dados e faça a busca scrapy crawl no repositório do querido-diario. Após isso, é possível...

Acesse os diários baixados através desse link: **http://localhost:9000/minio/queridodiariobucket**

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
