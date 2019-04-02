FROM python:3.7-slim as base

COPY ./requirements.txt /requirements.txt
COPY ./jwt_server.py /app/__main__.py

RUN pip3 install -r /requirements.txt

EXPOSE 8000

CMD python3 /app https://YOUR_DOMAIN/identity scope1 scope2
