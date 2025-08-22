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
# go to http://s3:9001/login
CHANGE_ME for user and password

For s3 setup you need to create an alias for s3 to `127.0.0.1`
   on MacOS run:

```sh
printf '\n127.0.0.1\ts3\n' | sudo tee -a /etc/hosts
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

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


## Dockerized setup

```bash
docker compose -f docker-compose.full.yml up -d
# If you encounter an error stating that the pod name already exists, simply rerun the command.
docker compose -f docker-compose.full.yml up -d
./scripts/ignite_app.sh
```