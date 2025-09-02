FROM nikolaik/python-nodejs:python3.8-nodejs20-slim

RUN apt-get update -y && apt-get upgrade -y
RUN apt-get -y install supervisor sudo

COPY ./wait-for-it.sh /usr/local/bin/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh

RUN pip install --upgrade pip
COPY ./requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY ./main/js/package*.json /code/main/js/
RUN npm install --prefix /code/main/js

COPY . /code
WORKDIR /code

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

ENTRYPOINT [ "sh", "entrypoint.sh" ]
