FROM python:3.9-slim-buster

WORKDIR /app

COPY ./app .

RUN pip3 --no-cache-dir install -r requirements.txt