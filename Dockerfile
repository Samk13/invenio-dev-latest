# ===== Version knobs =====
ARG ALPINE_VERSION=3.22.1
ARG PYTHON_SERIES=3.12
ARG NODE_IMAGE=node:22-alpine
ARG JS_PACKAGE_MANAGER=pnpm@10.8.1
ARG BUILD_EXTRAS="--extra sentry"

# ===== Common paths =====
ARG WORKING_DIR=/opt/invenio
ARG VIRTUAL_ENV=/opt/env
ARG INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance

# ===============
# 1) NODE + PNPM 
# ===============
FROM ${NODE_IMAGE} AS node_tools
ARG JS_PACKAGE_MANAGER
ENV JS_PACKAGE_MANAGER=${JS_PACKAGE_MANAGER}
RUN corepack enable && corepack prepare "${JS_PACKAGE_MANAGER}" --activate

# ===============
# 2) COMMON BASE 
# ===============
FROM alpine:${ALPINE_VERSION} AS app-base
ARG WORKING_DIR
ARG VIRTUAL_ENV
ARG INVENIO_INSTANCE_PATH

ENV UV_FROZEN=1 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_REQUIRE_HASHES=1 \
    UV_VERIFY_HASHES=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_MANAGED_PYTHON=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    VIRTUAL_ENV=${VIRTUAL_ENV} \
    WORKING_DIR=${WORKING_DIR} \
    UV_CACHE_DIR=/opt/.cache/uv \
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} \
    PATH=${VIRTUAL_ENV}/bin:/usr/local/bin:$PATH \
    INVENIO_INSTANCE_PATH=${INVENIO_INSTANCE_PATH}

WORKDIR ${WORKING_DIR}

# ===================
# 3) SOURCE SNAPSHOT 
# ===================
FROM app-base AS app-sources

COPY site ./site
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}/
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./translations/ ${INVENIO_INSTANCE_PATH}/translations/
# Counting on dockerignore to exclude unnecessary files
COPY . .

# =========================================
# 4) PYTHON BUILDER (toolchain + Node)
# =========================================
FROM app-base AS builder
ARG PYTHON_SERIES
ARG BUILD_EXTRAS

# System & build deps
RUN apk add --no-cache \
    "python3~=${PYTHON_SERIES}" "python3-dev~=${PYTHON_SERIES}" \
    git bash uv openssl \
    cairo \
    autoconf automake libtool build-base gcc musl-dev linux-headers \
    libxml2-dev libxslt-dev xmlsec-dev xmlsec \
    file binutils

# Bring Node + Corepack/pnpm (preserve layout/symlinks)
COPY --from=node_tools /usr/local/ /usr/local/

# Python venv + dirs
RUN uv venv "${VIRTUAL_ENV}" && mkdir -p "${INVENIO_INSTANCE_PATH}" /opt/.cache/uv

# Bring full sources + instance first
COPY --from=app-sources ${WORKING_DIR} ${WORKING_DIR}
COPY --from=app-sources ${INVENIO_INSTANCE_PATH} ${INVENIO_INSTANCE_PATH}

# Install all dependencies including workspace in one go
RUN --mount=type=cache,target=/opt/.cache/uv \
    uv sync --frozen --no-dev ${BUILD_EXTRAS}

# ---------- Frontend build (pnpm via Corepack) ----------
ENV INVENIO_WEBPACKEXT_NPM_PKG_CLS=pynpm:PNPMPackage \
    PNPM_HOME=/root/.local/share/pnpm
ENV PATH=${PNPM_HOME}:/usr/local/bin:${PATH}

RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    set -eux; \
    mkdir -p "${INVENIO_INSTANCE_PATH}/static" "${INVENIO_INSTANCE_PATH}/assets"; \
    cp -r ./static/. "${INVENIO_INSTANCE_PATH}/static/"; \
    cp -r ./assets/. "${INVENIO_INSTANCE_PATH}/assets/"; \
    uv run invenio collect --verbose; \
    uv run invenio webpack buildall; \
    uv cache clean; \
    rm -rf \
      "${INVENIO_INSTANCE_PATH}/assets/node_modules" \
      "${INVENIO_INSTANCE_PATH}/assets/.pnpm-store" \
      "${INVENIO_INSTANCE_PATH}/assets/.npm"

# ===========
# 6) RUNTIME 
# ===========
FROM app-base AS runtime
ARG PYTHON_SERIES
ARG IMAGE_BUILD_TIMESTAMP
ARG SENTRY_RELEASE

ENV UV_NO_CACHE=1 \
    INVENIO_IMAGE_BUILD_TIMESTAMP="${IMAGE_BUILD_TIMESTAMP}" \
    SENTRY_RELEASE="${SENTRY_RELEASE}"

# Runtime deps only
RUN apk add --no-cache \
    "python3~=${PYTHON_SERIES}" \
    libxslt xmlsec cairo \
    uwsgi-python3 \
    fontconfig ttf-dejavu \
    bash

# Non-root runtime user
RUN adduser -D -H invenio

# Bring venv + built app tree (includes instance with uwsgi*.ini and built assets)
COPY --from=builder --chown=invenio:invenio ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder --chown=invenio:invenio ${WORKING_DIR} ${WORKING_DIR}

USER invenio
ENTRYPOINT ["bash", "-c"]
