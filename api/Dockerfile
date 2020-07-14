# Dockerfile for API service
FROM python:3

MAINTAINER Jason Ashby "jashby2@gmail.com"

WORKDIR /usr/src/app

RUN apt-get -y update

COPY api.py requirements.txt /usr/src/app/
COPY cflib /usr/src/app/cflib

RUN mkdir -p /usr/src/app/uploads && chmod 750 /usr/src/app/uploads

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./api.py" ]