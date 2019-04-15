FROM python:3.7-slim as base

ENV CONTAINER_USER="jwt" \
    HOME_DIR="/app" \
    JWT_SERVER_PORT=8000 \
    JWT_AUDIANCE= \
    JWT_ISSUER= \
    JWT_KEY_URL= \
    JWT_SCOPE_PARAM=scope \
    JWT_SCOPE=

COPY ./requirements.txt /requirements.txt
COPY ./jwt_server.py ${HOME_DIR}/__main__.py
RUN pip3 install -r /requirements.txt

# add unprivileged user
RUN useradd -d ${HOME_DIR} -M -s /bin/sh ${CONTAINER_USER} && \
    chown -R ${CONTAINER_USER} ${HOME_DIR}

USER ${CONTAINER_USER}
WORKDIR ${HOME_DIR}


EXPOSE ${JWT_SERVER_PORT}
CMD python3 ${HOME_DIR}
