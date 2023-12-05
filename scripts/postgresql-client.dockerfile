FROM docker.io/bitnami/postgresql:15.4.0-debian-11-r10

COPY files/queridodiario_dump.sql /

COPY scripts/postgresql-client-entrypoint /entrypoint
ENTRYPOINT ["/entrypoint"]

