
ARG ALPINE_VERSION=3.22.1
ARG NODE_IMAGE=node:22-alpine
ARG JS_PACKAGE_MANAGER=pnpm@10.8.1

# Paths - define base path first
ARG WORKING_DIR=/opt/invenio
ARG VIRTUAL_ENV=/opt/env
ARG INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance

# ================================
# 1) NODE + PNPM STAGE
# ================================
FROM ${NODE_IMAGE} AS node_tools
ARG JS_PACKAGE_MANAGER
ENV JS_PACKAGE_MANAGER=${JS_PACKAGE_MANAGER}
# Prepare pnpm version with Corepack
RUN corepack enable && corepack prepare "${JS_PACKAGE_MANAGER}" --activate

# =========================================
# 2) PYTHON BUILDER (full toolchain + Node)
# =========================================
FROM alpine:${ALPINE_VERSION} AS builder

# Redeclare ARGs for this stage
ARG WORKING_DIR=/opt/invenio
ARG VIRTUAL_ENV=/opt/env
ARG INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance

# Core env
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=${VIRTUAL_ENV} \
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} \
    WORKING_DIR=${WORKING_DIR} \
    INVENIO_INSTANCE_PATH=${INVENIO_INSTANCE_PATH} \
    PATH=${VIRTUAL_ENV}/bin:/usr/local/bin:$PATH \
    PYTHONPATH=${VIRTUAL_ENV}/lib/python3.12:$PATH \
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

# System + build deps (Node toolchain copied in after apk)
RUN apk update && apk add --no-cache \
    python3>3.12 python3-dev>3.12 \
    git bash uv openssl \
    cairo \
    autoconf automake libtool build-base gcc musl-dev linux-headers \
    libxml2-dev libxslt-dev xmlsec-dev xmlsec \
    file binutils

# Bring Node + Corepack (+ prepared pnpm) from node_tools
COPY --from=node_tools /usr/local/bin /usr/local/bin
COPY --from=node_tools /usr/local/lib /usr/local/lib
COPY --from=node_tools /usr/local/include /usr/local/include
COPY --from=node_tools /usr/local/share /usr/local/share
# (This keeps Node confined to the builder stage only.)

# Python venv + dirs
RUN uv venv ${VIRTUAL_ENV} && \
    mkdir -p ${INVENIO_INSTANCE_PATH} /opt/.cache/uv
WORKDIR ${WORKING_DIR}/src

# ---------- Python deps (locked, no dev) ----------
ARG BUILD_EXTRAS="--extra sentry"
RUN --mount=type=cache,target=/opt/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} \
    uv sync --no-dev --no-install-workspace --no-editable $BUILD_EXTRAS

# ---------- Copy invenio instance ----------
# (Assumes .dockerignore excludes unwanted stuff.)
COPY site ./site
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations ${INVENIO_INSTANCE_PATH}/translations
COPY . .

# ---------- Install workspace packages ----------
RUN --mount=type=cache,target=/opt/.cache/uv \
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} \
    uv sync --frozen --no-dev $BUILD_EXTRAS

# ---------- Frontend build ----------
# Tell invenio to use pnpm
ENV INVENIO_WEBPACKEXT_NPM_PKG_CLS=pynpm:PNPMPackage
# Optional (helps pnpm cache performance in builder only)
ENV PNPM_HOME=/root/.local/share/pnpm
ENV PATH="${PNPM_HOME}:/usr/local/bin:${PATH}"

RUN cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    uv run invenio collect --verbose && \
    uv run invenio webpack buildall && \
    # PRUNE heavy frontend caches from instance after build
    rm -rf ${INVENIO_INSTANCE_PATH}/assets/node_modules \
           ${INVENIO_INSTANCE_PATH}/assets/.pnpm-store \
           ${INVENIO_INSTANCE_PATH}/assets/.npm \
           /root/.npm "${PNPM_HOME}" "$(pnpm store path || echo /root/.pnpm-store)" || true && \
    pnpm cache delete || true && \
    # Shrink Python: strip .so + clean uv cache (keeps venv intact)
    find "${VIRTUAL_ENV}" -name "*.so" -exec strip --strip-unneeded {} + || true && \
    uv cache clean || true

# =================================
# 3) RUNTIME (lean, no build deps)
# =================================
FROM alpine:${ALPINE_VERSION} AS frontend

# Redeclare ARGs for this stage
ARG WORKING_DIR=/opt/invenio
ARG VIRTUAL_ENV=/opt/env
ARG INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance

# Runtime env
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    VIRTUAL_ENV=${VIRTUAL_ENV} \
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} \
    WORKING_DIR=${WORKING_DIR} \
    INVENIO_INSTANCE_PATH=${INVENIO_INSTANCE_PATH} \
    PATH=${VIRTUAL_ENV}/bin:$PATH \
    UV_NO_CACHE=1

# Build args (kept)
ARG IMAGE_BUILD_TIMESTAMP
ARG SENTRY_RELEASE
ENV INVENIO_IMAGE_BUILD_TIMESTAMP="${IMAGE_BUILD_TIMESTAMP}" \
    SENTRY_RELEASE="${SENTRY_RELEASE}"

# Runtime deps ONLY (no -dev)
RUN apk update && apk add --no-cache \
    python3>3.12 \
    libxslt xmlsec cairo \
    uwsgi-python3 \
    fontconfig ttf-dejavu \
    bash

# Create user first so COPY --chown works
RUN adduser -D -H invenio

# Copy venv + instance from builder with correct ownership
COPY --from=builder --chown=invenio:invenio ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder --chown=invenio:invenio ${INVENIO_INSTANCE_PATH} ${INVENIO_INSTANCE_PATH}

WORKDIR ${WORKING_DIR}/src

# ---- KEEP “copy part” the same (overrides/instance bits) ----
COPY --chown=invenio:invenio site ./site
COPY --chown=invenio:invenio ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY --chown=invenio:invenio ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY --chown=invenio:invenio ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY --chown=invenio:invenio ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY --chown=invenio:invenio ./translations ${INVENIO_INSTANCE_PATH}/translations
COPY --chown=invenio:invenio . .

USER invenio
ENTRYPOINT [ "bash", "-c" ]
