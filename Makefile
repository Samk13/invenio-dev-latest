.DEFAULT_GOAL := help

VENV_PATH := $(CURDIR)/.venv
YES ?= 0
S3_ENDPOINT_URL ?= $(or $(INVENIO_S3_ENDPOINT_URL),https://localhost:9000)

export UV_PROJECT_ENVIRONMENT := $(VENV_PATH)
# Celery does not load .env.
export AWS_CA_BUNDLE ?= $(CURDIR)/docker/nginx/test.crt

define activate-venv
	if ! test -f "$(VENV_PATH)/bin/activate"; then \
	  echo 'Missing .venv. Run make install first.' >&2; \
	  exit 1; \
	fi; \
	. "$(VENV_PATH)/bin/activate"
endef

# Activation and execution share one shell. Bootstrap skips activation.
define run-command
	@set -eu; \
	$(if $(filter bootstrap,$(2)),unset VIRTUAL_ENV,$(activate-venv)); \
	printf 'Project: %s\nVenv name: %s\nVenv path: %s\n' \
	  "$(CURDIR)" "$$(basename "$${VIRTUAL_ENV:-none}")" "$${VIRTUAL_ENV:-none}"; \
	$(1)
endef

define confirm-reset
	if test "$(YES)" != "1"; then \
	  printf '%s Continue [y/N]? ' '$(1)'; \
	  read -r answer; \
	  case "$$answer" in y|Y|yes|YES) ;; *) echo 'Cancelled.'; exit 1 ;; esac; \
	fi
endef

.PHONY: help full-reset clean install run stop services-setup-dev renew-dev-certs s3-setup

help:
	@printf '%s\n' \
	  'make install             Install the instance.' \
	  'make services-setup-dev  Reset local data and configure S3.' \
	  'make run / stop          Start the app / stop services.' \
	  'make s3-setup            Configure bucket/CORS without resetting data.' \
	  'make renew-dev-certs     Renew certificates only when needed.' \
	  'make clean               Delete .venv and uv.lock.' \
	  'make full-reset          Clean, install, reset services, and run.' \
	  'Use YES=1 to skip reset confirmation.'

# Separate recipe lines keep destructive steps ordered, even with make -j.
full-reset:
	$(call run-command,$(call confirm-reset,WARNING: deletes .venv and uv.lock and resets local data.),bootstrap)
	@$(MAKE) clean
	@$(MAKE) install
	@$(MAKE) services-setup-dev YES=1
	@$(MAKE) run

clean:
	$(call run-command,rm -rf "$(VENV_PATH)" uv.lock,bootstrap)

install:
	$(call run-command,uv venv "$(VENV_PATH)",bootstrap)
	$(call run-command,uv run --active invenio-cli install)

run:
	$(call run-command,invenio-cli run)

stop:
	$(call run-command,invenio-cli services stop)

services-setup-dev:
	$(call run-command,$(call confirm-reset,WARNING: resets local application data.); invenio-cli services setup -f -N)
	@$(MAKE) s3-setup
	@echo 'Setup complete. Start the app with make run.'

renew-dev-certs:
	$(call run-command,bash scripts/renew_dev_certs.sh,bootstrap)

s3-setup:
	$(call run-command, \
	  echo 'Waiting for RustFS at $(S3_ENDPOINT_URL)...'; \
	  curl --silent --show-error --fail --output /dev/null \
	    --connect-timeout 2 --max-time 5 \
	    --retry 30 --retry-all-errors --retry-delay 2 --retry-max-time 90 \
	    --cacert "$$AWS_CA_BUNDLE" '$(S3_ENDPOINT_URL)/health'; \
	  python scripts/s3/configure_cors.py --create-bucket --endpoint '$(S3_ENDPOINT_URL)')
