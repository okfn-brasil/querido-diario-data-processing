# Build stage for dependencies
FROM docker.io/python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update -y && \
    apt-get -y install \
        build-essential \
        libpq-dev \
        curl \
        git && \
    curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
    apt-get -y install git-lfs && \
    git lfs install && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# Download ML model in builder stage
RUN python -c "import sentence_transformers; sentence_transformers.SentenceTransformer('neuralmind/bert-base-portuguese-cased').save('/tmp/bert-model')" && \
    rm -rf ~/.cache/huggingface ~/.cache/torch

# Runtime stage
FROM docker.io/python:3.11-slim

ENV USER=gazette
ENV USER_HOME=/home/$USER
ENV WORKDIR=/mnt/code

# Install only runtime dependencies
RUN addgroup --system $USER && \
    adduser --system --ingroup $USER $USER --home $USER_HOME && \
    apt-get update -y && \
    apt-get -y install \
        libpq5 \
        wait-for-it && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    mkdir $WORKDIR

ENV PYTHONPATH=$WORKDIR

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy ML model from builder
COPY --from=builder --chown=$USER:$USER /tmp/bert-model $USER_HOME/models/bert-base-portuguese-cased

# Switch to non-root user
USER $USER

# Copy application code
COPY --chown=$USER:$USER . $WORKDIR
WORKDIR $WORKDIR
