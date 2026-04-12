# Build arguments for multiarch support
ARG TARGETARCH=amd64
ARG TARGETOS=linux
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=latest

# Production image using pre-built base with all dependencies
# Base image contains: Python 3.14, all requirements.txt dependencies, ML models
FROM ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest
ARG TARGETARCH
ARG TARGETOS
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Labels for OCI image metadata
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.version="${VERSION}"

ENV USER=gazette
ENV USER_HOME=/home/$USER
ENV WORKDIR=/mnt/code

# Switch to non-root user (user already exists in base image)
USER $USER

# Copy application code
COPY --chown=$USER:$USER . $WORKDIR
WORKDIR $WORKDIR
