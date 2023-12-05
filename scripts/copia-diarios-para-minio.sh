#!/bin/sh

# Configure o mc com seu endpoint MinIO, Access Key e Secret Key
mc alias set myminio $MINIO_ACCESS_URL $MINIO_ACCESS_KEY $MINIO_SECRET_KEY

# Copie os arquivos para o bucket desejado
mc cp --recursive /files/ myminio/$MINIO_ACCESS_BUCKET/

echo "Arquivos copiados com sucesso!"
