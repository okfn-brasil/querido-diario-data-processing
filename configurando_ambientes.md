## Como os Projetos se relacionam

O repositório [querido-diario-data-processing](https://github.com/okfn-brasil/querido-diario-data-processing) tem como objetivo gerar buscas mais assertivas para o usuário por meio do uso de técnicas de processamento de linguagem natural. O processo desse repositório pode ser referenciado a partir da imagem da Infraestrutura do Querido Diário no [[fluxograma_1.png]]. As partes referentes à indexação e extração do texto são responsabilidade desse repositório em específico. Afinal, para ter os documentos em formato de texto (.txt) disponíveis na [plataforma](https://queridodiario.ok.org.br/) é necessário que seja feito um processamento desse conteúdo (os PDFs coletados previamente pelo repositório [querido-diario](https://github.com/okfn-brasil/querido-diario)).

Esse é o objetivo principal mas não é o único, já que além da possibilidade da colaboração por meio do desenvolvimento, é também possível aplicar as técnicas de PLN em um _dataset_ específico.

## Configurando seu ambiente de Desenvolvimento
 
Sempre fique ligado(a) ao documento de [Contribuição](https://github.com/okfn-brasil/querido-diario-comunidade/blob/main/.github/CONTRIBUTING.md#ecossistema), nele é possível verificar as exigências básicas como formatação _black_, configuração de ambiente seguro, detalhamento nas _[[issues e pull requests]]_. Lembre-se também que as **issues e pull requests são uma parte da documentação do projeto**!  
 
Sabendo desses pontos, é necessário configurar o ambiente de trabalho. Existem três diferentes sistemas operacionais que são compatíveis com o ambiente desenvolvido: Linux (o padrão e raíz), Windows e Mac. Vamos explorar cada um deles.

### Linux

Se você já trabalha com Linux seguir as orientações de instalação contidas no [repositório](https://github.com/okfn-brasil/querido-diario-data-processing) serão suficientes para instalar o ambiente.

Alguns possíveis problemas que talvez precisem de um cuidado é relacionado à conexão do ecossistema com o [[querido-diario]]. Veja em [[conectar ao querido-diario]].

### Windows
##### Utilizando WSL

Para utlizar essa etapa é necessário instalar o WSL na sua máquina Windows e instalar um sistema operacional. Veja esse tutorial de [[Instalando WSL]] caso tenha dúvidas.

Dentro da sua máquina Linux já é possível seguir as instruções de instalação do ambiente contidas no repositório em [Setup](). Instale o Podman e inicie o ambiente virtual. Um comando de cada vez.

~~~Linux
 sudo apt-get update
 ## sudo apt update && sudo apt upgrade  ##testar
 sudo apt-get -y install podman
 
 sudo apt install python3.10-venv
 python3 -m venv .venv
 source .venv/Scripts/activate  ### Ativando o ambiente virtual

 sudo apt install make          ### Caso apresente erro de instalação
 make build                     ### Somente a 1° vez
 make setup
 ~~~

Teste para ver se o seu ambiente funciona:
~~~Linux
make shell-database
~~~

![[Pasted image 20231005100446.png]]
![[Pasted image 20231005100534.png]]

Após essa etapa é necessário **[[conectar ao querido-diario]]** ao banco de dados gerados pelo repositório [[querido-diario]] o qual é responsável por extrair os diários oficiais. Se a conexão não for feita, esse repositório não possui documentos para processar. Faça o fork do repositório [[querido-diario]] e [[querido-diario-data-processing]] na sua conta do Github e a partir daí faça o clone para a sua máquina Linux desses repositórios.
### Mac

...
