# InvenioRDM Development Environment

Welcome to your InvenioRDM development instance. This repository contains a complete development setup for the latest InvenioRDM build.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Setup Options](#setup-options)
  - [Native Development Setup](#native-development-setup)
  - [Dockerized Setup](#dockerized-setup)
- [Configuration](#configuration)
- [Local Package Development](#local-package-development)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before starting, ensure you have the following installed:

- Python 3.12+
- uv 0.8.x+
- Node.js 22+
- pnpm 10.15.x+
- Docker & Docker Compose (for containerized setup)
- Git

## Quick Start

The fastest way to get started is using the dockerized setup:

```bash
# Start all services
docker compose -f docker-compose.full.yml down && \
docker compose -f docker-compose.full.yml up -d --build
# > **Note:** If you encounter an error about existing pod names, simply rerun the commands.
docker compose -f docker-compose.full.yml up -d
# Initialize the application
./scripts/ignite_app.sh
```

## Setup Options

### Native Development Setup

For local development with more control over the environment:

1. **Create and activate virtual environment:**
   ```console
   uv venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```console
   uv pip install invenio-cli
   uv run invenio-cli install
   ```

3. **Setup services:**
   ```console
   uv run invenio-cli services setup -f -N
   ```

4. **Configure S3 storage (macOS):**
   ```bash
   printf '\n127.0.0.1\ts3\n' | sudo tee -a /etc/hosts
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder
   ```

### Dockerized Setup

For a complete containerized environment:

```bash
# Start all services (database, search, cache, etc.)
docker compose -f docker-compose.full.yml up -d

# Initialize the application
./scripts/ignite_app.sh
```

## Configuration

### S3 Storage Setup

After starting the services, you may need to configure the default S3 bucket:

1. Navigate to http://s3:9001/login
2. Use the default credentials: `CHANGE_ME` (both username and password)
3. Create necessary buckets as required

### Environment Variables

Key configuration files:
- `invenio.cfg` - Main application configuration
- `docker-compose.yml` - Service orchestration
- `pyproject.toml` - Python dependencies

## Local Package Development

If you're developing local InvenioRDM packages, you can install them using:

```console
# Adjust paths in the script as needed
./install_local_packages.sh
```

> **Important:** Make sure to adjust the package paths in the script before running.

## Documentation

For comprehensive guides on configuration, customization, and deployment:

- 📚 [InvenioRDM Documentation](https://inveniordm.docs.cern.ch/)
- 🔧 [Configuration Guide](https://inveniordm.docs.cern.ch/install/)

## Troubleshooting

### Common Issues

1. **Port conflicts:** Ensure ports 80, 443, 5432, 9200, 6379, and 9001 are available
2. **Permission issues:** Make sure Docker has appropriate permissions
3. **Memory issues:** Ensure Docker has at least 4GB RAM allocated

### Useful Commands

```bash
# View logs
docker compose -f docker-compose.full.yml logs

# Stop all services
docker compose -f docker-compose.full.yml down

# Restart services
docker compose -f docker-compose.full.yml restart

# Clean up (removes volumes)
docker compose -f docker-compose.full.yml down -v
```

---

For more help, please refer to the [InvenioRDM Community Forum](https://github.com/inveniosoftware/invenio-app-rdm/discussions) or check the [troubleshooting guide](https://inveniordm.docs.cern.ch/install/troubleshooting/).