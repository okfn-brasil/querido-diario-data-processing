PT/BR [Tutorial geral](https://github.com/Luisa-Coelho/qd-data-processing/blob/readme_update/tutorial.md) | [Configurando os diferentes ambientes](https://github.com/Luisa-Coelho/qd-data-processing/blob/readme_update/configurando_ambientes.md) | [Conectando ao querido-diario](https://github.com/Luisa-Coelho/qd-data-processing/blob/readme_update/conectando_qd.md)

EN/US

## O processamento de dados

O repositório [querido-diario-data-processing](https://github.com/okfn-brasil/querido-diario-data-processing) tem como objetivo gerar buscas mais assertivas para o usuário por meio do uso de técnicas de processamento de linguagem natural. O processo desse repositório pode ser referenciado a partir da imagem da Infraestrutura do Querido Diário na Figura abaixo.
![image](https://github.com/Luisa-Coelho/qd-data-processing/assets/87907716/cd6b5589-f4e7-45a0-86a9-5cbb0bf14cb7)

As partes referentes à indexação e extração do texto são responsabilidade desse repositório em específico. Afinal, para ter os documentos em formato de texto (.txt) disponíveis na [plataforma](https://queridodiario.ok.org.br/) é necessário que seja feito um processamento desse conteúdo (os PDFs coletados previamente pelo repositório [querido-diario](https://github.com/okfn-brasil/querido-diario)).

Veja a estrutura completa do projeto [aqui](https://docs.queridodiario.ok.org.br/pt/latest/).

### Entendendo a estrutura do querido-diario-data-processing

1. Montando o ambiente de trabalho

A pasta "scripts" são responsáveis pelo ambiente de trabalho.

2. Extração do texto

"data_extraction"

3. Processamento do texto

A pasta "tasks" 

4. Armazenamento

"database" e "storage"
