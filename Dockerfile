#
# Copyright (C) 2024 CERN.
# Copyright (C) 2024 KTH Royal Institute of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# Image info:
# - Base image: python:3.12-alpine3.20
# - Build time: ~5 minutes
# - Image size: ~1.25GB
# - Node.js: LTS (Not pinned)
# - Python: 3.12

# -------------------------------------------------
# Builder Stage
# -------------------------------------------------
ARG LINUX_VERSION=3.20
ARG PYTHON_VERSION=3.12
ARG BUILDPLATFORM=linux/amd64

FROM --platform=$BUILDPLATFORM python:${PYTHON_VERSION}-alpine${LINUX_VERSION} AS builder

ENV WORKING_DIR=/opt/invenio
ENV INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

WORKDIR ${INVENIO_INSTANCE_PATH}

    # Copy the site directory
COPY site ${INVENIO_INSTANCE_PATH}/site/

# Install build dependencies
RUN apk add --no-cache \
    nodejs \
    npm \
    cairo \
    gcc \
    musl-dev \
    linux-headers && \
    pip install --break-system-packages --no-cache-dir pipenv

RUN mkdir -p "${INVENIO_INSTANCE_PATH}"
# Copy Pipfile and Pipfile.lock first to leverage Docker cache
COPY Pipfile Pipfile.lock ./

# Install Python dependencies
RUN pipenv install --deploy --system --extra-pip-args="--break-system-packages --no-cache-dir" && \
    pipenv --clear

# Copy application files
COPY site ${INVENIO_INSTANCE_PATH}/site/
COPY docker/uwsgi/ ${INVENIO_INSTANCE_PATH}/
COPY invenio.cfg ${INVENIO_INSTANCE_PATH}/
COPY app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY assets/ /tmp/assets/
COPY static/ /tmp/static/
COPY templates/ /tmp/templates/
COPY translations/ /tmp/translations/

# Build frontend assets
RUN invenio collect --verbose && \
    mkdir -p assets templates translations && \
    cp -r /tmp/assets/ ${INVENIO_INSTANCE_PATH}/ && \
    invenio webpack buildall && \
    cp -r /tmp/static/ ${INVENIO_INSTANCE_PATH}/ && \
    cp -r /tmp/templates/ ${INVENIO_INSTANCE_PATH}/ && \
    cp -r /tmp/translations/ ${INVENIO_INSTANCE_PATH}/

# Clean up build dependencies and caches
RUN rm -rf ${INVENIO_INSTANCE_PATH}/assets/node_modules && \
    npm cache clean --force && \
    apk del gcc musl-dev linux-headers && \
    rm -rf /var/cache/apk/* /root/.cache/pip

# -------------------------------------------------
# Final Stage
# -------------------------------------------------
FROM --platform=$BUILDPLATFORM python:${PYTHON_VERSION}-alpine${LINUX_VERSION}

ENV WORKING_DIR=/opt/invenio
ENV INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

WORKDIR ${INVENIO_INSTANCE_PATH}

# Create a non-root user and group
RUN addgroup -S invenio && \
    adduser -S -G invenio -h ${WORKING_DIR} invenio

# Install runtime dependencies
RUN apk add --no-cache \
    imagemagick \
    font-dejavu \
    cairo \
    bash

# Copy necessary files from the builder stage
COPY . ${INVENIO_INSTANCE_PATH}/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION%.*}/site-packages/ /usr/local/lib/python${PYTHON_VERSION%.*}/site-packages/
COPY --from=builder ${INVENIO_INSTANCE_PATH}/ ${INVENIO_INSTANCE_PATH}/

# Set file permissions
RUN mkdir -p ${INVENIO_INSTANCE_PATH}/data ${INVENIO_INSTANCE_PATH}/archive && \
    chown -R invenio:invenio ${INVENIO_INSTANCE_PATH}

# Switch to the non-root user
USER invenio

# Set entrypoint
ENTRYPOINT ["bash", "-c"]
