FROM docker.io/python:3.8

ENV USER gazette
ENV USER_HOME /home/$USER
ENV WORKDIR /mnt/code

RUN adduser --system $USER --home $USER_HOME && \
	apt-get update -y && \
  curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
	apt-get -y install git-lfs wait-for-it && \
	apt-get clean && \
  git lfs install && \
	mkdir $WORKDIR

ENV PYTHONPATH $WORKDIR
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . $WORKDIR
WORKDIR $WORKDIR
USER $USER

RUN python -c "import sentence_transformers; sentence_transformers.SentenceTransformer('neuralmind/bert-base-portuguese-cased').save('"$USER_HOME"/models/bert-base-portuguese-cased')"
