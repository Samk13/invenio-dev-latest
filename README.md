# Dev latest-build 

Welcome to your InvenioRDM instance.

## Getting started

Run the following commands in order to start your new InvenioRDM instance:

```console
uv venv
source .venv/bin/activate
uv pip install invenio-cli
uv run invenio-cli install
uv run invenio-cli services setup -f -N
# You might need to setup default bucket for file storage
# go to http://localhost:9001/login
CHANGE_ME for user and password

uv run invenio-cli run
```

# Install local packages

If you have local packages that you want to install, you can run the following command:

```console
# make sure to adjust the path for locally installed packages in the script

./install_local_packages.sh
```

## Documentation

To learn how to configure, customize, deploy and much more, visit
the [InvenioRDM Documentation](https://inveniordm.docs.cern.ch/).
