**English (US)** | [Português (BR)](/docs/README.md) 

<p align="center">
  <a href="https://queridodiario.ok.org.br/sobre" target="_blank"> <img alt="Querido Diário" src="/docs/images/querido-diario-logo.png" width="200">
  </a>
</p>

# Data processing
Within the [Querido Diário ecosystem](https://docs.queridodiario.ok.org.br/en/latest/contributing/contribution-guide.html#ecosystem), this repository is responsible for document transformations and loading them into appropriate storages.

Learn more about the [technologies](https://queridodiario.ok.org.br/en-US/tecnologia) and the [history](https://queridodiario.ok.org.br/en-US/sobre) of the project.

# Summary
- [How to contribute](#how-to-contribute)
- [Development environment](#development-environment)
- [How to run](#how-to-run)
- [Support](#support)
- [Acknowledgments](#acknowledgements)
- [Open Knowledge Brasil](#open-knowledge-brasil)
- [License](#license)

# How to contribute
<p>  
  <a href="https://www.catarse.me/queridodiario-okbr" target="_blank"> 
    <img alt="catarse" src="https://img.shields.io/badge/Catarse-Apoie%20o%20projeto-orange?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB2ZXJzaW9uPSIxLjIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgdmlld0JveD0iMCAwIDMyNSA0NTUiIHdpZHRoPSIzMjUiIGhlaWdodD0iNDU1Ij4KCTx0aXRsZT5sb2dvLXYtY29yLXBvc2l0aXZvLWFpPC90aXRsZT4KCTxzdHlsZT4KCQkuczAgeyBmaWxsOiAjMTdhMzM4IH0gCgkJLnMxIHsgZmlsbDogIzdkYjkzZCB9IAoJCS5zMiB7IGZpbGw6ICNmMmJmMDAgfSAKCQkuczMgeyBmaWxsOiAjZjE5MTA2IH0gCgkJLnM0IHsgZmlsbDogI2VhNjYwYiB9IAoJCS5zNSB7IGZpbGw6ICNkZTMyODEgfSAKCTwvc3R5bGU+Cgk8ZyBpZD0iTGF5ZXIgMSI+CgkJPGcgaWQ9IiZsdDtHcm91cCZndDsiPgoJCQk8cGF0aCBpZD0iJmx0O1BhdGgmZ3Q7IiBjbGFzcz0iczAiIGQ9Im01Ni40IDI1Ni40cS0xLjggMy4xLTMuNCA2LjRjLTE1LjQgMzMuMS00LjcgNjMuMSAxNC44IDkyLjQgMTEuNiAxNy40IDguNiAzNi40LTEuOSA0Ny4zLTYgNi4zLTE0LjUgOS44LTIzLjIgOS43LTQuNSAwLTkuMS0wLjktMTMuNS0zLTYuMy0yLjktMTUuMS05LjEtMjIuMi0yOC43LTguOS0yNC4yLTkuMS01MS42IDIuNi03Ni44IDEwLjEtMjEuNiAyNi45LTM3LjggNDYuOC00Ny4zeiIvPgoJCQk8cGF0aCBpZD0iJmx0O1BhdGgmZ3Q7IiBjbGFzcz0iczEiIGQ9Im00Ni41IDMwNS44YzAuNSAyLjYgMSA1LjIgMS43IDcuOCAxMC41IDM4LjcgNDAuNyA1Ni41IDc3LjggNjcuNCAyMi4xIDYuNSAzMyAyNC43IDMxLjkgNDEuMi0wLjcgOS42LTUuMyAxOC41LTEyLjcgMjQuNi0zLjggMy4yLTguNCA1LjctMTMuNSA3LTcuNCAyLTE5LjIgMy0zOS4xLTguNC0yNC41LTE0LjItNDQuMS0zNy4yLTUyLTY2LjctNi44LTI1LjItNC4xLTUwLjggNS45LTcyLjl6Ii8+CgkJCTxwYXRoIGlkPSImbHQ7UGF0aCZndDsiIGNsYXNzPSJzMiIgZD0ibTczLjIgMzU0LjVjMi4yIDEuOCA0LjUgMy42IDYuOSA1LjMgMzYuMiAyNS4zIDc0LjMgMTguOSAxMTMuMiAxLjggMjMuMi0xMC4xIDQ1LjMtMi41IDU2IDEyLjIgNi4zIDguNiA4LjYgMTkuNCA2LjggMjkuNy0xIDUuNC0zLjEgMTAuNy02LjUgMTUuNS00LjggNi45LTE0IDE2LjEtMzguOSAyMC41LTMwLjcgNS40LTYzLjQtMC4xLTkwLjktMTkuNC0yMy42LTE2LjUtMzkuNC0zOS45LTQ2LjYtNjUuNnoiLz4KCQkJPHBhdGggaWQ9IiZsdDtQYXRoJmd0OyIgY2xhc3M9InMzIiBkPSJtMTMwLjEgMzc2LjZxNC43IDAuMSA5LjUtMC40YzQ4LjQtNC4zIDc2LTM2LjUgOTYuNy03OC41IDEyLjQtMjUgMzYuNC0zNC4xIDU1LjgtMjkuMyAxMS40IDIuOCAyMSAxMC4yIDI2LjcgMjAuMyAzIDUuMiA1IDExLjEgNS41IDE3LjYgMC45IDkuMi0wLjQgMjMuNC0xOC4zIDQ0LjctMjIgMjYuMy01My41IDQ0LjgtOTAuMyA0OC0zMS41IDIuOC02MS40LTUuOC04NS42LTIyLjR6Ii8+CgkJCTxwYXRoIGlkPSImbHQ7UGF0aCZndDsiIGNsYXNzPSJzNCIgZD0ibTE5My42IDM1NS4xYzIuNy0yLjIgNS4zLTQuNiA3LjgtNy4xIDM3LjctMzcuOCAzOC4xLTg0LjUgMjUuOS0xMzQuNS03LjItMjkuOCA2LjUtNTQuNSAyNi4zLTY0LjIgMTEuNS01LjYgMjQuOS02LjEgMzYuOC0xLjggNi4zIDIuMyAxMi4xIDUuOSAxNy4xIDExIDcuMiA3LjEgMTYuMiAyMC4xIDE2LjMgNTAuNiAwIDM3LjctMTMuNSA3NS42LTQyLjIgMTA0LjMtMjQuNiAyNC43LTU1LjkgMzguNi04OCA0MS43eiIvPgoJCQk8cGF0aCBpZD0iJmx0O1BhdGgmZ3Q7IiBjbGFzcz0iczUiIGQ9Im0yMzEuOSAyOTJjMC44LTQuNCAxLjQtOC45IDEuOC0xMy41IDYtNjkuMi0zMi42LTExNi04Ni41LTE1NS43LTMyLjItMjMuNi0zOS4xLTU5LjYtMjcuNS04NS44IDYuNy0xNS4zIDE5LjctMjcgMzUuMi0zMi42IDguMS0yLjkgMTctNC4yIDI2LjEtMy40IDEzLjIgMS4xIDMzIDYuNSA1OC42IDM2LjkgMzEuNSAzNy41IDQ5LjcgODYuNSA0NS4xIDEzOS4xLTMuOSA0NS4xLTIzLjQgODUuMS01Mi44IDExNXoiLz4KCQk8L2c+Cgk8L2c+Cjwvc3ZnPg==">
  </a>
</p> 

Thank you for considering contributing to Querido Diário! :tada:

You can find how to do so in the [CONTRIBUTING.md](/docs/CONTRIBUTING-en-US.md)!

Additionally, check out the [Querido Diário documentation](https://docs.queridodiario.ok.org.br/en/latest/) to help you.

# Development environment

To set up the development environment, the [podman](https://podman.io/) container manager is required.

From a terminal open in the repository root directory, use the following command sequence to build the images and set up the pod and resource containers on a Linux operating system:

```console
make build
make setup
```

For more details about the setup, read ["how to set up the development environment"](/docs/CONTRIBUTING-en-US.md#how-to-configure-the-development-environment).

# How to run

To run any pipeline, it's necessary to populate the metadata database (Postgres) and download documents to the object storage (Minio). For this, we can use the [scraper repository](https://github.com/okfn-brasil/querido-diario) according to the [end-to-end setup documentation](https://docs.queridodiario.ok.org.br/en/latest/contributing/end-to-end-configuration.html#generating-data-with-spiders).

After running the scrapers, we can run the text extraction pipeline, which will populate the search engine (Opensearch) with the main index (full text of gazettes) and thematic indexes (gazette excerpts related to specific topics). This is done with the command:

```console
make re-run
```

By default, this pipeline will process all documents in the database, regardless of whether they have been previously processed. If you want to change this behavior, modify the `EXECUTION_MODE` environment variable in `envvars`.

With the extracted texts, we can also run the data aggregation pipeline, which provides the gazette texts in CSV format. To do so, run:

```console
make aggregate-gazettes
```

The results can be found in the search engine and object storage. Find tips on how to access them in this [documentation](https://docs.queridodiario.ok.org.br/en/latest/contributing/end-to-end-configuration.html#environment-usage-tips).

# Support
<p>  
  <a href="https://go.ok.org.br/discord" target="_blank">
    <img alt="Discord Invite" src="https://img.shields.io/badge/Discord-Entre%20no%20servidor-blue?style=for-the-badge&logo=discord" >
  </a>
</p>

Join our [community channel](https://go.ok.org.br/discord) to discuss projects, ask questions, request help with contributions, and chat about civic innovation in general.

# Acknowledgments
The application was initially developed with the people from the software studio [Jurema](https://jurema.la/).

This project is maintained by Open Knowledge Brasil and made possible thanks to technical communities, [Civic Innovation Ambassadors](https://embaixadoras.ok.org.br/), volunteers, and financial donors, as well as partner universities, supporting companies, and funders.

Get to know [who supports Querido Diário](https://queridodiario.ok.org.br/apoie#quem-apoia).

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

[Open Knowledge Brasil](https://ok.org.br/) is a non-profit civil society organization whose mission is to use and develop civic tools, projects, public policy analyses, and data journalism to promote open knowledge in various fields of society.

All the work produced by OKBR is freely available.

# License

Code licensed under the [MIT License](/LICENSE.md).
