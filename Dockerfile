FROM python:3.8

RUN adduser --system gazette

RUN apt-get update -y && \
	apt-get -y install default-jre wait-for-it && \
	apt-get clean

# install Apache Tika
RUN curl -o /tika-server.jar http://archive.apache.org/dist/tika/tika-server-1.24.1.jar && \
	curl -o /tika-app.jar http://archive.apache.org/dist/tika/tika-app-1.24.1.jar  && \
	chmod 755 /tika-server.jar && \
	chmod 755 /tika-app.jar 

RUN mkdir /mnt/code
COPY . /mnt/code
WORKDIR /mnt/code
ENV PYTHONPATH=/mnt/code

RUN pip install --no-cache-dir -r requirements.txt

USER gazette
