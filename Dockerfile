# ===== Version knobs (easy to bump) =====
ARG ALPINE_VERSION=3.22.1
ARG PYTHON_SERIES=3.12
ARG NODE_IMAGE=node:22-alpine
ARG JS_PACKAGE_MANAGER=pnpm@10.8.1

# ===== Common paths =====
ARG WORKING_DIR=/opt/invenio
ARG VIRTUAL_ENV=/opt/env
ARG INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance

# ================================
# 1) NODE + PNPM STAGE (builder-only)
# ================================
FROM ${NODE_IMAGE} AS node_tools
ARG JS_PACKAGE_MANAGER
ENV JS_PACKAGE_MANAGER=${JS_PACKAGE_MANAGER}
RUN corepack enable && corepack prepare "${JS_PACKAGE_MANAGER}" --activate

# =========================================
# 2) PYTHON BUILDER (full toolchain + Node)
# =========================================
FROM alpine:${ALPINE_VERSION} AS builder
# Re-declare only what this stage needs
ARG PYTHON_SERIES
ARG WORKING_DIR
ARG VIRTUAL_ENV
ARG INVENIO_INSTANCE_PATH

# Define env in safe order (no undefined refs)
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
ENV VIRTUAL_ENV=${VIRTUAL_ENV}
ENV UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV}
ENV WORKING_DIR=${WORKING_DIR}
ENV INVENIO_INSTANCE_PATH=${INVENIO_INSTANCE_PATH}
ENV PATH=${VIRTUAL_ENV}/bin:/usr/local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_CACHE_DIR=/opt/.cache/uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_FROZEN=1
ENV UV_LINK_MODE=copy
ENV UV_NO_MANAGED_PYTHON=1
ENV UV_SYSTEM_PYTHON=1
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_REQUIRE_HASHES=1
ENV UV_VERIFY_HASHES=1
ENV CFLAGS="-Wno-error=incompatible-pointer-types"

# System & build deps (builder only)
RUN apk update && apk add --no-cache \
    "python3~=${PYTHON_SERIES}" "python3-dev~=${PYTHON_SERIES}" \
    git bash uv openssl \
    cairo \
    autoconf automake libtool build-base gcc musl-dev linux-headers \
    libxml2-dev libxslt-dev xmlsec-dev xmlsec \
    file binutils

# Bring Node + Corepack/pnpm into builder
COPY --from=node_tools /usr/local/bin /usr/local/bin
COPY --from=node_tools /usr/local/lib /usr/local/lib
COPY --from=node_tools /usr/local/include /usr/local/include
COPY --from=node_tools /usr/local/share /usr/local/share

# Python venv + dirs
RUN uv venv "${VIRTUAL_ENV}" && mkdir -p "${INVENIO_INSTANCE_PATH}" /opt/.cache/uv
WORKDIR ${WORKING_DIR}/src

# Python deps (locked, no dev)
ARG BUILD_EXTRAS="--extra sentry"
RUN --mount=type=cache,target=/opt/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-dev --no-install-workspace --no-editable $BUILD_EXTRAS

# Copy instance to build
COPY site ./site
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations ${INVENIO_INSTANCE_PATH}/translations
COPY . .

# Install workspace (incl. ./site)
RUN --mount=type=cache,target=/opt/.cache/uv \
    uv sync --frozen --no-dev $BUILD_EXTRAS

# Frontend build (pnpm via Corepack) + prune
ENV INVENIO_WEBPACKEXT_NPM_PKG_CLS=pynpm:PNPMPackage
ENV PNPM_HOME=/root/.local/share/pnpm
ENV PATH=${PNPM_HOME}:/usr/local/bin:${PATH}
RUN cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    uv run invenio collect --verbose && \
    uv run invenio webpack buildall && \
    rm -rf ${INVENIO_INSTANCE_PATH}/assets/node_modules \
           ${INVENIO_INSTANCE_PATH}/assets/.pnpm-store \
           ${INVENIO_INSTANCE_PATH}/assets/.npm \
           /root/.npm "${PNPM_HOME}" "$(pnpm store path || echo /root/.pnpm-store)" || true && \
    pnpm cache delete || true && \
    find "${VIRTUAL_ENV}" -name "*.so" -exec strip --strip-unneeded {} + 2>/dev/null || true && \
    uv cache clean || true

# =================================
# 3) RUNTIME (lean, no build deps)
# =================================
FROM alpine:${ALPINE_VERSION} AS frontend
# Re-declare what this stage needs
ARG PYTHON_SERIES
ARG WORKING_DIR
ARG VIRTUAL_ENV
ARG INVENIO_INSTANCE_PATH
ARG IMAGE_BUILD_TIMESTAMP
ARG SENTRY_RELEASE

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
ENV VIRTUAL_ENV=${VIRTUAL_ENV}
ENV UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV}
ENV WORKING_DIR=${WORKING_DIR}
ENV INVENIO_INSTANCE_PATH=${INVENIO_INSTANCE_PATH}
ENV PATH=${VIRTUAL_ENV}/bin:$PATH
ENV UV_NO_CACHE=1
ENV INVENIO_IMAGE_BUILD_TIMESTAMP="${IMAGE_BUILD_TIMESTAMP}"
ENV SENTRY_RELEASE="${SENTRY_RELEASE}"

# Runtime deps
RUN apk update && apk add --no-cache \
    "python3~=${PYTHON_SERIES}" \
    libxslt xmlsec cairo \
    uwsgi-python3 \
    fontconfig ttf-dejavu \
    bash

# Create user; use COPY --chown instead of chown layer
RUN adduser -D -H invenio

# Bring venv + built instance
COPY --from=builder --chown=invenio:invenio ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder --chown=invenio:invenio ${INVENIO_INSTANCE_PATH} ${INVENIO_INSTANCE_PATH}

WORKDIR ${WORKING_DIR}/src

# ===== Copy instance files =====
COPY --chown=invenio:invenio site ./site
COPY --chown=invenio:invenio ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY --chown=invenio:invenio ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY --chown=invenio:invenio ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY --chown=invenio:invenio ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY --chown=invenio:invenio ./translations ${INVENIO_INSTANCE_PATH}/translations
COPY --chown=invenio:invenio . .

USER invenio
ENTRYPOINT ["bash", "-c"]
