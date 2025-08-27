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
    # Python and uv configuration
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

# Install system dependencies
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

# Create virtual environment and working directory
RUN uv venv ${VIRTUAL_ENV} && \
    mkdir -p ${INVENIO_INSTANCE_PATH} && \
    mkdir -p /opt/.cache/uv

WORKDIR ${WORKING_DIR}/src

# Install Python dependencies using uv
ARG BUILD_EXTRAS="--extra sentry"
RUN --mount=type=cache,target=/opt/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} \
    uv sync --no-dev --no-install-workspace --no-editable $BUILD_EXTRAS

# Copy application files
COPY site ./site
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations ${INVENIO_INSTANCE_PATH}/translations
COPY . .

# Install workspace packages
RUN --mount=type=cache,target=/opt/.cache/uv \
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} \
    uv sync --frozen --no-dev $BUILD_EXTRAS

# Build static assets
RUN cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose && \
    invenio webpack buildall

# FRONTEND STAGE - Minimal runtime image
FROM alpine:${ALPINE_VERSION} AS frontend

# Environment variables
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    VIRTUAL_ENV=/opt/env \
    UV_PROJECT_ENVIRONMENT=/opt/env \
    WORKING_DIR=/opt/invenio \
    INVENIO_INSTANCE_PATH=/opt/invenio/var/instance \
    PATH=/opt/env/bin:$PATH \
    UV_NO_CACHE=1

# Application build args
ARG IMAGE_BUILD_TIMESTAMP
ARG SENTRY_RELEASE
ENV INVENIO_IMAGE_BUILD_TIMESTAMP="${IMAGE_BUILD_TIMESTAMP}" \
    SENTRY_RELEASE="${SENTRY_RELEASE}"

# Install runtime dependencies
RUN apk update && \
    apk add --update --no-cache --repository=https://dl-cdn.alpinelinux.org/alpine/edge/community \
    python3>3.12 \
    libxslt-dev \
    xmlsec \
    cairo \
    uwsgi-python3 \
    fontconfig \
    ttf-dejavu \
    bash \
    uv

# Setup virtual environment and directories
RUN uv venv ${VIRTUAL_ENV} && \
    mkdir -p ${INVENIO_INSTANCE_PATH} ${VIRTUAL_ENV} ${WORKING_DIR}/src/saml/idp/cert && \
    adduser -D -H invenio && \
    rm -f ${VIRTUAL_ENV}/bin/python && \
    ln -s /usr/bin/python3 ${VIRTUAL_ENV}/bin/python

# Copy built application from builder stage
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder ${INVENIO_INSTANCE_PATH} ${INVENIO_INSTANCE_PATH}

WORKDIR ${WORKING_DIR}/src

COPY site ./site

COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations ${INVENIO_INSTANCE_PATH}/translations
COPY ./ .

# Install site package
RUN UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} uv pip install -e ./site && \
    chown -R invenio:invenio ${WORKING_DIR} && \
    echo "Image build timestamp ${INVENIO_IMAGE_BUILD_TIMESTAMP}"

USER invenio

ENTRYPOINT [ "bash", "-c" ]