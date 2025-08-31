FROM docker.io/python:3.11-slim

ENV USER=gazette
ENV USER_HOME=/home/$USER
ENV WORKDIR=/mnt/code

RUN adduser --system $USER --home $USER_HOME && \
	apt-get update -y && \
	apt-get -y install \
		build-essential \
		libpq-dev \
		curl \
		git \
		wait-for-it && \
  curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
	apt-get -y install git-lfs && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/* && \
  git lfs install && \
	mkdir $WORKDIR

ENV PYTHONPATH=$WORKDIR

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Switch to non-root user for model download
USER $USER

# Create models directory and download model
RUN mkdir -p $USER_HOME/models && \
    python -c "import sentence_transformers; sentence_transformers.SentenceTransformer('neuralmind/bert-base-portuguese-cased').save('$USER_HOME/models/bert-base-portuguese-cased')"

# Copy application code
COPY --chown=$USER:$USER . $WORKDIR
WORKDIR $WORKDIR
