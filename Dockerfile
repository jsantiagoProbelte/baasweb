FROM ubuntu:16.04
LABEL maintainer="BaasWebApp container <appsvc-images@microsoft.com>"
FROM python:3.9.16

RUN apt-get update && apt-get install -y python3-pip python3-dev && apt-get clean

RUN apt-get install -y libpq-dev 

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip3 install -r requirements.txt
ADD . /code/

EXPOSE 8081
CMD ["gunicorn", "--bind", ":8081", "--workers", "3", "baaswebapp.wsgi:application"]
