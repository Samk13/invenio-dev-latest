# BUILDER STAGE - Build dependencies and assets
ARG ALPINE_VERSION=3.22.1
FROM alpine:${ALPINE_VERSION} AS builder

# Common environment variables
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PIPENV_VERBOSITY=-1 \
    VIRTUAL_ENV=/opt/env \
    UV_PROJECT_ENVIRONMENT=/opt/env \
    WORKING_DIR=/opt/invenio \
    INVENIO_INSTANCE_PATH=/opt/invenio/var/instance \
    PYTHONUSERBASE=/opt/env \
    PATH=/opt/env/bin:$PATH \
    PYTHONPATH=/opt/env/lib/python3.12:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/opt/.cache/uv \
    UV_COMPILE_BYTECODE=1 \
    UV_FROZEN=1 \
    UV_LINK_MODE=copy \
    UV_NO_MANAGED_PYTHON=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_REQUIRE_HASHES=1 \
    UV_VERIFY_HASHES=1 \
    # xmlsec compatibility
    CFLAGS="-Wno-error=incompatible-pointer-types"

# System deps for building (node only in builder)
RUN apk update && \
    apk add --update --no-cache --repository=https://dl-cdn.alpinelinux.org/alpine/edge/community \
    python3>3.12 \
    python3-dev>3.12 \
    nodejs>20 \
    npm>10 \
    git \
    cairo \
    autoconf \
    automake \
    bash \
    build-base \
    file \
    gcc \
    libtool \
    libxml2-dev \
    libxslt-dev \
    linux-headers \
    xmlsec-dev \
    xmlsec \
    uv \
    pnpm \
    openssl

# Virtualenv and dirs
RUN uv venv ${VIRTUAL_ENV} && \
    mkdir -p ${INVENIO_INSTANCE_PATH} && \
    mkdir -p /opt/.cache/uv

WORKDIR ${WORKING_DIR}/src

# Install Python deps (non-editable, no workspace yet)
ARG BUILD_EXTRAS="--extra sentry"
RUN --mount=type=cache,target=/opt/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} \
    uv sync --no-dev --no-install-workspace --no-editable $BUILD_EXTRAS

# Copy application sources
COPY site ./site
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations ${INVENIO_INSTANCE_PATH}/translations
COPY . .

# Install workspace packages into the venv (this installs ./site)
RUN --mount=type=cache,target=/opt/.cache/uv \
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} \
    uv sync --frozen --no-dev $BUILD_EXTRAS

# Build static assets and PRUNE heavy build artifacts
RUN cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose && \
    invenio webpack buildall && \
    # prune frontend/node caches and stores from the instance
    rm -rf ${INVENIO_INSTANCE_PATH}/assets/node_modules \
           ${INVENIO_INSTANCE_PATH}/assets/.pnpm-store \
           ${INVENIO_INSTANCE_PATH}/assets/.npm && \
    # clean global caches (best-effort)
    npm cache clean --force || true && \
    pnpm store prune || true && \
    pnpm cache delete || true && \
    rm -rf /root/.npm /root/.cache/pnpm || true && \
    # shrink python cache too
    uv cache clean || true

# FRONTEND STAGE - Minimal runtime image
FROM alpine:${ALPINE_VERSION} AS frontend

# Environment
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    VIRTUAL_ENV=/opt/env \
    UV_PROJECT_ENVIRONMENT=/opt/env \
    WORKING_DIR=/opt/invenio \
    INVENIO_INSTANCE_PATH=/opt/invenio/var/instance \
    PATH=/opt/env/bin:$PATH \
    UV_NO_CACHE=1

# Build args (kept)
ARG IMAGE_BUILD_TIMESTAMP
ARG SENTRY_RELEASE
ENV INVENIO_IMAGE_BUILD_TIMESTAMP="${IMAGE_BUILD_TIMESTAMP}" \
    SENTRY_RELEASE="${SENTRY_RELEASE}"

# Runtime deps ONLY (no -dev headers here)
RUN apk update && \
    apk add --update --no-cache --repository=https://dl-cdn.alpinelinux.org/alpine/edge/community \
    python3>3.12 \
    libxslt \
    xmlsec \
    cairo \
    uwsgi-python3 \
    fontconfig \
    ttf-dejavu \
    bash

# Create runtime user up front so we can use COPY --chown
RUN adduser -D -H invenio

# Copy venv and instance from builder with ownership set at copy-time
COPY --from=builder --chown=invenio:invenio ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder --chown=invenio:invenio ${INVENIO_INSTANCE_PATH} ${INVENIO_INSTANCE_PATH}

WORKDIR ${WORKING_DIR}/src

# KEEP your existing small copies — but set ownership at copy-time
COPY --chown=invenio:invenio site ./site
COPY --chown=invenio:invenio ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY --chown=invenio:invenio ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY --chown=invenio:invenio ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY --chown=invenio:invenio ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY --chown=invenio:invenio ./translations ${INVENIO_INSTANCE_PATH}/translations
COPY --chown=invenio:invenio . .

# Do NOT create another venv or reinstall; the builder venv is complete.
# Do NOT chown recursively; COPY --chown already handled it.

USER invenio
ENTRYPOINT [ "bash", "-c" ]
