# Use uma imagem base. Aqui, estou usando alpine por ser leve e suficiente para este caso.
FROM alpine:latest

# Instale o MinIO Client (mc)
RUN wget https://dl.min.io/client/mc/release/linux-amd64/mc \
    && chmod +x mc \
    && mv mc /usr/bin

# Copie os arquivos que você deseja transferir para o bucket no container
# Supondo que os arquivos estejam no diretório "files" do contexto de build
COPY files/diarios/ /files/

# Script que executa a cópia
COPY scripts/copia-diarios-para-minio.sh /copy-script.sh
RUN chmod +x /copy-script.sh

# Comando que será executado quando o container iniciar
CMD ["/copy-script.sh"]
