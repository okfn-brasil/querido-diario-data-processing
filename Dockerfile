# Production image using pre-built base with all dependencies
# Base image contains: Python 3.11, all requirements.txt dependencies, ML models
FROM ghcr.io/okfn-brasil/querido-diario-data-processing/base:latest

ENV USER=gazette
ENV USER_HOME=/home/$USER
ENV WORKDIR=/mnt/code

# Switch to non-root user (user already exists in base image)
USER $USER

# Copy application code
COPY --chown=$USER:$USER . $WORKDIR
WORKDIR $WORKDIR
