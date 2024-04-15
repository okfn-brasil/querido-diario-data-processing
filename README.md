# Querido Diário - Processamento de Dados

Este repositório contém todo o código do pipeline de processamento usado pelo
projeto Querido Diário para analisar os diários extraídos pelos raspadores.

Aqui, você encontrará os códigos usados no pipeline, juntamente com o Helm
chart usado para instalá-lo em um cluster Kubernetes.

# Sumário

- [Como contribuir](#como-contribuir)
- [Suporte](#suporte)
- [Agradecimentos](#agradecimentos)
- [Open Knowledge Brasil](#open-knowledge-brasil)
- [Licença](#licença)


## Como contribuir 

Para informações sobre contribuições e de como rodar o pipeline, leia o
[CONTRIBUTING.md](./CONTRIBUTING.md). Mas se você já tem instalado na máquina o
minikube, docker, ctlptl e o tilt, execute:

```console
$ make cluster
$ tilt up --stream
```

Além disso, consulte a [documentação do Querido
Diário](https://docs.queridodiario.ok.org.br/pt-br/latest/) para te ajudar. 

# Suporte 
<p>  
  <a href="https://go.ok.org.br/discord" target="_blank">
    <img alt="Discord Invite" src="https://img.shields.io/badge/Discord-Entre%20no%20servidor-blue?style=for-the-badge&logo=discord" >
  </a>
</p>

Ingresse em nosso [canal de comunidade](https://go.ok.org.br/discord) para
trocas sobre os projetos, dúvidas, pedidos de ajuda com contribuição e
conversar sobre inovação cívica em geral.


# Agradecimentos

Este projeto é mantido pela Open Knowledge Brasil e possível graças às
comunidades técnicas, às [Embaixadoras de Inovação
Cívica](https://embaixadoras.ok.org.br/), às pessoas voluntárias e doadoras
financeiras, além de universidades parceiras, empresas apoiadoras e
financiadoras.

Conheça [quem apoia o Querido
Diário](https://queridodiario.ok.org.br/apoie#quem-apoia).

# Open Knowledge Brasil

<p>
  <a href="https://twitter.com/okfnbr" target="_blank">
    <img alt="Twitter Follow" src="https://img.shields.io/badge/Twitter-_-blue?style=for-the-badge&logo=twitter">
  </a>
  <a href="https://www.instagram.com/openknowledgebrasil/" target="_blank">
    <img alt="Instagram Follow" src="https://img.shields.io/badge/Instagram-_-red?style=for-the-badge&logo=instagram">
  </a>
  <a href="https://www.linkedin.com/company/open-knowledge-brasil" target="_blank">
    <img alt="LinkedIn Follow" src="https://img.shields.io/badge/LinkedIn-_-9cf?style=for-the-badge&logo=linkedin">
  </a>
</p>

A [Open Knowledge Brasil](https://ok.org.br/) é uma organização da sociedade
civil sem fins lucrativos, cuja missão é utilizar e desenvolver ferramentas
cívicas, projetos, análises de políticas públicas, jornalismo de dados para
promover o conhecimento livre nos diversos campos da sociedade. 

Todo o trabalho produzido pela OKBR está disponível livremente.

# Licença

Código licenciado sob a [Licença MIT](LICENSE.md).


