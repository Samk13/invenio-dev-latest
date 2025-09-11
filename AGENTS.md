This file provides agent-focused guidance for working with the ivenioRDM repository.
Humans should start with README.md. Coding agents should follow the instructions here.

## Project overview

ivenioRDM is a research data management (RDM) platform.
Monorepo with multiple packages, each with its own package.json.
Primary stack: JavaScript, React, pnpm workspace tooling.

## Development environment
Make sure that your .venv is set up and activated.
Use `uv run invenio-cli run` to run invenio instance
use `uv run invenio shell` for interactive python shell with invenio context
use `uv run invenio shell python_file.py` to execute python file with invenio context
use `ruff format` to format the code

Always ask for instructions if you are unsure about something.
