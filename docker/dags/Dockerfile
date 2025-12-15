FROM apache/airflow:latest
LABEL org.opencontainers.image.authors="mail@bsantanna.me"
ENV REFRESHED_AT=2025-11-15

USER root

RUN apt update -qq && \
    apt install -yqq --no-install-recommends git && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN cd /tmp/ && \
    git clone https://github.com/bsantanna/quaks.git quaks && \
    cd /tmp/quaks && chown airflow:root /tmp/quaks/ && \
    cp -a /tmp/quaks/dags ${AIRFLOW_HOME}/dags/

USER airflow
