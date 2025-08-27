# Dockerfile that builds a fully functional image of your app.
#
# This image installs all Python dependencies for your application. It's based
# on Alpine Linux for minimal size and includes Python, Node.js, npm, and
# standard libraries Invenio usually needs.

# BUILDER STAGE - Build dependencies and assets
FROM alpine:edge AS builder

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

ENV PYTHONUNBUFFERED=1
ENV PIPENV_VERBOSITY=-1
ENV VIRTUAL_ENV=/opt/env
ENV UV_PROJECT_ENVIRONMENT=/opt/env
ENV WORKING_DIR=/opt/invenio
ENV INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance
ENV PYTHONUSERBASE=$VIRTUAL_ENV
ENV PATH=$VIRTUAL_ENV/bin:$PATH
ENV PYTHONPATH=$VIRTUAL_ENV/lib/python3.12:$PATH

# Python and uv configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/opt/.cache/uv \
    UV_COMPILE_BYTECODE=1 \
    UV_FROZEN=1 \
    UV_LINK_MODE=copy \
    UV_NO_MANAGED_PYTHON=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_REQUIRE_HASHES=1 \
    UV_VERIFY_HASHES=1

RUN apk update
RUN apk add --update --no-cache --repository=https://dl-cdn.alpinelinux.org/alpine/edge/community \
    "python3>3.12" \
    "python3-dev>3.12" \
    "nodejs>20" \
    "npm>10" \
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

RUN uv venv ${VIRTUAL_ENV}

# necessary because of https://github.com/xmlsec/python-xmlsec/pull/325
ENV CFLAGS="-Wno-error=incompatible-pointer-types"

# Note: xmlsec and lxml will be installed later with the other dependencies

WORKDIR ${WORKING_DIR}/src

RUN mkdir -p ${INVENIO_INSTANCE_PATH}

# Install Python dependencies using uv
ARG BUILD_EXTRAS="--extra sentry"
RUN --mount=type=cache,target=/opt/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} CFLAGS="-Wno-error=incompatible-pointer-types" \
    uv sync --no-dev --no-install-workspace --no-editable $BUILD_EXTRAS

COPY site ./site

COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations ${INVENIO_INSTANCE_PATH}/translations
COPY ./ .

# Make sure workspace packages are installed
RUN --mount=type=cache,target=/opt/.cache/uv \
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} uv sync --frozen --no-dev $BUILD_EXTRAS

RUN cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose && \
    invenio webpack buildall

# FRONTEND STAGE - Minimal runtime image
FROM alpine:edge AS frontend

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

ENV VIRTUAL_ENV=/opt/env
ENV UV_PROJECT_ENVIRONMENT=/opt/env
ENV WORKING_DIR=/opt/invenio
ENV INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance
ENV PATH=$VIRTUAL_ENV/bin:$PATH

# application build args to be exposed as environment variables
ARG IMAGE_BUILD_TIMESTAMP
ARG SENTRY_RELEASE

# Expose random sha to uniquely identify this build
ENV INVENIO_IMAGE_BUILD_TIMESTAMP="'${IMAGE_BUILD_TIMESTAMP}'"
ENV SENTRY_RELEASE=${SENTRY_RELEASE}

RUN apk update

# ttf-dejavu: for doi badges
RUN apk add --update --no-cache --repository=https://dl-cdn.alpinelinux.org/alpine/edge/community \
    "python3>3.12" \
    libxslt-dev \
    xmlsec \
    cairo \
    uwsgi-python3 \
    fontconfig \
    ttf-dejavu \
    bash \
    uv

RUN uv venv ${VIRTUAL_ENV}

RUN mkdir -p ${INVENIO_INSTANCE_PATH}
RUN mkdir -p ${VIRTUAL_ENV}
RUN mkdir -p ${WORKING_DIR}/src/saml/idp/cert

RUN adduser invenio --no-create-home --disabled-password

RUN rm -f ${VIRTUAL_ENV}/bin/python && ln -s /usr/bin/python3 ${VIRTUAL_ENV}/bin/python

# Copy built application from builder stage
COPY --from=builder ${VIRTUAL_ENV}/lib ${VIRTUAL_ENV}/lib
COPY --from=builder ${VIRTUAL_ENV}/bin ${VIRTUAL_ENV}/bin
COPY --from=builder ${INVENIO_INSTANCE_PATH}/app_data ${INVENIO_INSTANCE_PATH}/app_data
COPY --from=builder ${INVENIO_INSTANCE_PATH}/static ${INVENIO_INSTANCE_PATH}/static
COPY --from=builder ${INVENIO_INSTANCE_PATH}/translations ${INVENIO_INSTANCE_PATH}/translations
COPY --from=builder ${INVENIO_INSTANCE_PATH}/templates ${INVENIO_INSTANCE_PATH}/templates

WORKDIR ${WORKING_DIR}/src

COPY site ./site
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}/
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}/
COPY ./ .

# Copy built application from builder stage
COPY --from=builder ${VIRTUAL_ENV}/lib ${VIRTUAL_ENV}/lib
COPY --from=builder ${VIRTUAL_ENV}/bin ${VIRTUAL_ENV}/bin
COPY --from=builder ${INVENIO_INSTANCE_PATH}/app_data ${INVENIO_INSTANCE_PATH}/app_data
COPY --from=builder ${INVENIO_INSTANCE_PATH}/static ${INVENIO_INSTANCE_PATH}/static
COPY --from=builder ${INVENIO_INSTANCE_PATH}/translations ${INVENIO_INSTANCE_PATH}/translations
COPY --from=builder ${INVENIO_INSTANCE_PATH}/templates ${INVENIO_INSTANCE_PATH}/templates

# Ensure the site package is properly installed for the worker
RUN UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} uv pip install -e ./site
RUN chown -R invenio:invenio ${WORKING_DIR}

# We're not caching on a mount in production
ENV UV_NO_CACHE=1

RUN echo "Image build timestamp $INVENIO_IMAGE_BUILD_TIMESTAMP"

USER invenio

ENTRYPOINT [ "bash", "-c"]

# Final production image - alias for frontend 
FROM frontend AS production