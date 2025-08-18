ARG JS_PACKAGE_MANAGER=pnpm@10.8.1
ARG NODE_IMAGE=node:22-alpine
ARG PYTHON_BASE_IMAGE=ghcr.io/astral-sh/uv:0.6-python3.12-alpine

ARG WORKING_DIR=/opt/invenio
ARG INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance

# --- NODE.JS STAGE ---
FROM ${NODE_IMAGE} AS node
ARG JS_PACKAGE_MANAGER
ENV JS_PACKAGE_MANAGER=${JS_PACKAGE_MANAGER}
RUN corepack enable && corepack prepare ${JS_PACKAGE_MANAGER} --activate

# --- BASE SETUP STAGE ---
FROM ${PYTHON_BASE_IMAGE} AS python_base
ARG INVENIO_INSTANCE_PATH
ENV INVENIO_INSTANCE_PATH=${INVENIO_INSTANCE_PATH} \
LANG=en_US.UTF-8 \
LANGUAGE=en_US:en \
LC_ALL=en_US.UTF-8 \
# Compile Python files to .pyc bytecode files
UV_COMPILE_BYTECODE=1 \
# Copy Python files from cache mount, resolving symlink issues
UV_LINK_MODE=copy
ENV PATH="${INVENIO_INSTANCE_PATH}/.venv/bin:${PATH}"
RUN apk update && \
    apk add --no-cache \
    bash cairo \
    imagemagick util-linux

# --- BUILD APP STAGE ---
FROM python_base AS builder
WORKDIR ${INVENIO_INSTANCE_PATH}
RUN apk add --no-cache \
        gcc \
        musl-dev \
        linux-headers

# Copy Node.js runtime libraries and binaries
COPY --from=node /usr/lib /usr/lib
COPY --from=node /usr/local/bin /usr/local/bin
COPY --from=node /usr/local/lib /usr/local/lib
COPY --from=node /usr/local/include /usr/local/include
COPY --from=node /usr/local/share /usr/local/share

# Count on .dockerignore to exclude files
COPY . .

# Sync Python dependencies
RUN uv sync --locked && \
    uv cache clean

# --- FRONTEND BUILD ---
ENV INVENIO_WEBPACKEXT_NPM_PKG_CLS=pynpm:PNPMPackage
RUN uv run invenio collect --verbose && \
    mkdir -p assets templates translations site data archive && \
    uv run invenio webpack buildall && \
    rm -rf assets/node_modules && \
    # Experimental command!
    # https://pnpm.io/cli/cache-delete
    pnpm cache delete && \
    rm -rf "$(pnpm store path)" && \
    # Uwsgi config expected to be on instance level
    cp -a docker/uwsgi/. .

# --- RUNTIME STAGE ---
FROM python_base AS runtime

RUN addgroup -S invenio && \
    adduser -S -G invenio invenio

COPY --from=builder --chown=invenio:invenio \
    "${INVENIO_INSTANCE_PATH}" \
    "${INVENIO_INSTANCE_PATH}"

USER invenio
WORKDIR ${INVENIO_INSTANCE_PATH}

ENTRYPOINT ["bash", "-c"]