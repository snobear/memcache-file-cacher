# Dockerfile for test runs
FROM python:3

MAINTAINER Jason Ashby "jashby2@gmail.com"

WORKDIR /usr/src/app

RUN apt-get -y update

COPY test_api.py requirements.txt /usr/src/app/

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./test_api.py" ]