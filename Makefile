.DEFAULT_GOAL := help

S3_ENDPOINT_URL ?= $(if $(INVENIO_S3_ENDPOINT_URL),$(INVENIO_S3_ENDPOINT_URL),https://localhost:9000)

# Celery does not load .env; pass CA trust to all CLI child processes.
export AWS_CA_BUNDLE ?= $(CURDIR)/docker/certs/ca.pem

# GNU Make reserves -y and cannot use it as a custom confirmation flag.
YES ?= 0

.PHONY: help full-reset clean install run services-setup-dev setup-dev dev-certs dev-services s3-setup

help:
	@printf '%s\n' \
	  'make full-reset          Clean, install, reset services, and run (destructive).' \
	  'make clean               Remove .venv and uv.lock.' \
	  'make install             Install the instance with uv.' \
	  'make services-setup-dev  Generate certificates, reset services, and configure S3.' \
	  'make run                 Start the instance.' \
	  'make dev-certs           Generate development certificates if missing.' \
	  'make s3-setup            Create the S3 bucket and configure CORS (no data reset).' \
	  'Use YES=1 to skip confirmation (make reserves -y).'

# Confirm before deleting anything; execute sequentially even with make -j.
full-reset:
	@if test "$(YES)" != "1"; then \
	  printf 'WARNING: deletes .venv and uv.lock and resets local application data. Type y to continue [y/N] (or rerun with YES=1): ';  \
	  read -r answer; \
	  case "$$answer" in y|Y|yes|YES) ;; *) echo 'Cancelled.'; exit 1 ;; esac; \
	fi
	@$(MAKE) clean
	@$(MAKE) install
	@$(MAKE) services-setup-dev YES=1
	@$(MAKE) run

clean:
	rm -rf .venv uv.lock

install:
	uv venv
	. .venv/bin/activate && uv run invenio-cli install

run:
	. .venv/bin/activate && invenio-cli run

# Keep the previous command as an alias.
setup-dev: services-setup-dev

# Recursive calls keep the steps ordered, even with make -j.
services-setup-dev:
	@$(MAKE) dev-certs
	@$(MAKE) dev-services
	@$(MAKE) s3-setup
	@printf '%s\n' \
	  'Setup complete. Start or restart the app: make run' \
	  'RustFS console: https://localhost:9001/rustfs/console/auth/login/' \
	  'Default login: CHANGE_ME / CHANGE_ME (unless overridden).' \
	  'Before uploading, open and accept the development certificate warning:' \
	  'https://localhost:9000/health' \
	  'Accept the console certificate warning too if prompted.'

dev-certs:
	@if test -s docker/certs/cert.pem && test -s docker/certs/key.pem && test -s docker/certs/ca.pem; then \
	  echo 'Reusing existing development certificates.'; \
	else \
	  bash scripts/setup_dev_certs.sh; \
	fi

dev-services:
	@if test "$(YES)" != "1"; then \
	  printf 'WARNING: service setup resets local application data. Type y to continue [y/N] (or rerun with YES=1): ';  \
	  read -r answer; \
	  case "$$answer" in y|Y|yes|YES) ;; *) echo 'Cancelled.'; exit 1 ;; esac; \
	fi
	. .venv/bin/activate && invenio-cli services setup -f -N

s3-setup:
	@echo 'Waiting for RustFS at $(S3_ENDPOINT_URL)...'
	@attempt=0; until curl --silent --show-error --fail --connect-timeout 2 --max-time 5 \
	  --cacert "$${AWS_CA_BUNDLE:-docker/certs/ca.pem}" \
	  '$(S3_ENDPOINT_URL)/health' > /dev/null 2>&1; do \
	  attempt=$$((attempt + 1)); \
	  if test "$$attempt" -ge 30; then \
	    echo 'RustFS did not become ready. Check the endpoint, certificates, and container logs.'; exit 1; \
	  fi; \
	  sleep 2; \
	done
	uv run --no-sync python scripts/s3/configure_cors.py --create-bucket --endpoint '$(S3_ENDPOINT_URL)'
