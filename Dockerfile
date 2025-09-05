# Build stage for dependencies
FROM docker.io/python:3.11-slim AS builder

# Install build dependencies in single layer for better caching
RUN apt-get update -y && \
    apt-get -y install --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        git && \
    curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
    apt-get -y install --no-install-recommends git-lfs && \
    git lfs install && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy requirements first for better cache layering
COPY requirements.txt .

# Install Python dependencies with aggressive cleanup
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt && \
    pip cache purge && \
    find /root/.local -name "*.pyc" -delete && \
    find /root/.local -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Download ML model with cleanup
RUN python -c "import sentence_transformers; sentence_transformers.SentenceTransformer('neuralmind/bert-base-portuguese-cased').save('/tmp/bert-model')" && \
    rm -rf ~/.cache/huggingface ~/.cache/torch ~/.cache/pip

# Runtime stage
FROM docker.io/python:3.11-slim

ENV USER=gazette
ENV USER_HOME=/home/$USER
ENV WORKDIR=/mnt/code

# Install only runtime dependencies with cleanup
RUN addgroup --system $USER && \
    adduser --system --ingroup $USER $USER --home $USER_HOME && \
    apt-get update -y && \
    apt-get -y install --no-install-recommends \
        libpq5 \
        wait-for-it && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    mkdir $WORKDIR

ENV PYTHONPATH=$WORKDIR

# Copy Python packages from builder (using --user install path)
COPY --from=builder /root/.local /home/$USER/.local

# Copy ML model from builder
COPY --from=builder --chown=$USER:$USER /tmp/bert-model $USER_HOME/models/bert-base-portuguese-cased

# Ensure user has access to locally installed packages
ENV PATH=/home/$USER/.local/bin:$PATH

# Switch to non-root user
USER $USER

# Copy application code
COPY --chown=$USER:$USER . $WORKDIR
WORKDIR $WORKDIR
