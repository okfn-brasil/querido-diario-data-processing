FROM docker.io/python:3.8

ARG GAZETTE_UID
RUN adduser --system --uid $GAZETTE_UID gazette && \
	apt-get update -y && \
  curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
	apt-get -y install git-lfs wait-for-it && \
	apt-get clean && \
  git lfs install && \
	mkdir /mnt/code

COPY . /mnt/code
WORKDIR /mnt/code
ENV PYTHONPATH=/mnt/code

RUN pip install --no-cache-dir -r requirements.txt

USER gazette

RUN python -m spacy download pt_core_news_sm
RUN python -m nltk.downloader stopwords
RUN python -c "import sentence_transformers; sentence_transformers.SentenceTransformer('neuralmind/bert-base-portuguese-cased').save('"$HOME"/models/bert-base-portuguese-cased')"
