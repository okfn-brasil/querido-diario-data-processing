PT/BR [Tutorial geral](tutorial.md) | [Configurando os diferentes ambientes](configurando_ambientes.md) | [Conectando ao querido-diario](conectando_qd.md)

EN/US

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
