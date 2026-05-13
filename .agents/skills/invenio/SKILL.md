---
  name: invenio
  description: provides guidance for working with the invenioRDM repository
argument-hint: "commands to run instance run tests etc."
---

This file provides agent-focused guidance for working with the ivenioRDM repository.
Humans should start with README.md. Coding agents should follow the instructions here.

## Project overview

ivenioRDM is a research data management (RDM) platform.
Monorepo with multiple packages, each with its own package.json.
Primary stack: JavaScript, React, pnpm workspace tooling.

## Development environment
Make sure that your .venv is set up and activated.
you need to do that only once: `source .venv/bin/activate`
if you find issue starting the instance check docker containers with `docker ps` if there are same containers conflicting stop them with `docker stop <container_id>` and try again.
- start instance with `uv run invenio-cli run`
- to run scripts withing invenio context run `uv run invenio shell` to start an interactive python shell with invenio context or `uv run invenio shell python_file.py` to execute a python file with invenio context
to format code, use `ruff format` to format the code

Always ask for instructions if you are unsure about something.
