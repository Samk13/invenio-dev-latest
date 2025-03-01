# Dev latest-build

## Test install with uv and pnpm

### How to install


steps to use the new invenio-cli with all in:

1.) check that uv and pnpm are installed

2.) create a new my-site directory with the regular content as usual OR go into your current development my-site directory

2.a) deactivate the active environment

3.) create with uv a virtual environment with `uv venv --prompt uv-env && source .venv/bin/activate`

4.) install invenio-cli with `uv pip install invenio-cli`

5.) copy following text into the .invenio file into the cli section
  ```toml
  [cli]
  flavour = RDM
  python_package_manager = uv
  ```

6.) copy following text into the pyproject.toml file. the file should be created beside the invenio.cfg file

```toml
[project]
name = "InvenioRDM"
requires-python = ">= 3.12"
dynamic = ["version"]

dependencies = [
  "invenio-app-rdm[opensearch2]~=13.0.0b2.dev0",
  "uwsgi>=2.0",
  "uwsgitop>=0.11",
  "uwsgi-tools>=1.1.1",

  # have better invenio-cli
  "invenio-cli", # enables overrides

  # rspack
  "flask-webpackext",
  "invenio-assets",
]

[tool.setuptools]
py-modules = [] # necessary to make the packages with setup.py usable with uv

[tool.uv]
prerelease = "allow" # necessary only because of the "dev" tags in the invenio packages,
                     # caused by flask>3 and sqlalchemy>2, should be removed afterwards

# overrides packages from "dependencies"
[tool.uv.sources]
invenio-cli = { git = "https://github.com/utnapischtim/invenio-cli", branch = "WIP-merged-up-uv-ports-branches" }
flask-webpackext = { git = "https://github.com/utnapischtim/flask-webpackext", branch = "make-ready-for-rspack" }
invenio-assets = { git = "https://github.com/slint/invenio-assets", branch = "rspack" }
# invenio-cli = { path = "path/to/invenio-cli", editable = true } # would be local example

````

7.) run time invenio-cli install to install and to see how long it takes

8.) run time invenio-cli install again to see the behavior with hot cache


Runs wihout issues.
Setting before run the watch command: `export FLASK_DEBUG=1`
invenio-cli assets watch works without issues.
