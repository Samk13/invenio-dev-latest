# Dockerfile that builds a fully functional image of your app.
#
# This image installs all Python dependencies for your application. It's based
# on Almalinux (https://github.com/inveniosoftware/docker-invenio)
# and includes Pip, Pipenv, Node.js, NPM and some few standard libraries
# Invenio usually needs.

FROM registry.cern.ch/inveniosoftware/almalinux:1


RUN dnf install -y epel-release
RUN dnf update -y

# Install Python 3.12
RUN dnf install -y python3.12 python3.12-pip python3.12-devel

# Python and uv configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/opt/.cache/uv \
    UV_COMPILE_BYTECODE=1 \
    UV_FROZEN=1 \
    UV_LINK_MODE=copy \
    UV_NO_MANAGED_PYTHON=1 \
    UV_NO_MANAGED_PYTHON=1 \
    UV_NO_MANAGED_PYTHON=1 \
    UV_NO_MANAGED_PYTHON=1 \
    UV_NO_MANAGED_PYTHON=1 \
    UV_SYSTEM_PYTHON=1 \
    # Tell uv to use system Python
    UV_PROJECT_ENVIRONMENT=/usr/ \
    UV_PYTHON_DOWNLOADS=never \
    UV_REQUIRE_HASHES=1 \
    UV_VERIFY_HASHES=1

# Get latest version of uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python dependencies using uv
ARG BUILD_EXTRAS="--extra sentry"
RUN --mount=type=cache,target=/opt/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    UV_PROJECT_ENVIRONMENT=/opt/uv-env uv sync --no-dev --no-install-workspace --no-editable $BUILD_EXTRAS

# Add the virtual environment to PATH
ENV PATH="/opt/uv-env/bin:$PATH"

COPY site ./site

COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations ${INVENIO_INSTANCE_PATH}/translations
COPY ./ .

# Make sure workspace packages are installed (zenodo-rdm, zenodo-legacy)
RUN --mount=type=cache,target=/opt/.cache/uv \
    UV_PROJECT_ENVIRONMENT=/opt/uv-env uv sync --frozen --no-dev $BUILD_EXTRAS

# We're caching on a mount, so for any commands that run after this we
# don't want to use the cache (for image filesystem permission reasons)
ENV UV_NO_CACHE=1

# application build args to be exposed as environment variables
ARG IMAGE_BUILD_TIMESTAMP
ARG SENTRY_RELEASE

# Expose random sha to uniquely identify this build
ENV INVENIO_IMAGE_BUILD_TIMESTAMP="'${IMAGE_BUILD_TIMESTAMP}'"
ENV SENTRY_RELEASE=${SENTRY_RELEASE}

RUN echo "Image build timestamp $INVENIO_IMAGE_BUILD_TIMESTAMP"

RUN cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose  && \
    invenio webpack buildall

ENTRYPOINT [ "bash", "-lc"]