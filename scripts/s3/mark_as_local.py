# Copyright (C) 

import click
from flask.cli import with_appcontext
from invenio_app.cli import cli
from invenio_db import db
from invenio_rdm_records.records.models import RDMFileDraftMetadata
from rich.console import Console
from sqlalchemy.orm.attributes import flag_modified


@click.command("mark-as-local")
@with_appcontext
def mark_as_local():

    console = Console()
    console.print("[bold red]Marking file as local...[/bold red]")
    pid = console.input("Please enter the record PID: ") or "jn1wq-2k798"
    file_key = (
        console.input("Please enter the file key to mark as local: ")
        or "large_file.bin"
    )

    from invenio_rdm_records.records.models import RDMDraftMetadata  # noqa
    from invenio_pidstore.models import PersistentIdentifier  # noqa

    record_pid = (
        db.session.query(PersistentIdentifier)
        .filter_by(pid_type="recid", pid_value=pid)
        .first()
    )
    if not record_pid:
        console.print(f"[bold red]Record with PID {pid} not found.[/bold red]")
        return

    record_id = record_pid.object_uuid
    draft_file = (
        db.session.query(RDMFileDraftMetadata)
        .filter_by(record_id=record_id, key=file_key)
        .first()
    )
    if not draft_file:
        console.print(
            f"[bold red]File with key {file_key} not found in record {pid}.[/bold red]"
        )
        return
    draft_file.json["transfer"]["type"] = "L"
    flag_modified(draft_file, "json")
    db.session.commit()

    console.print("[green]File marked successfully as local.[/green]")


def run():
    cli.add_command(mark_as_local)
    cli.main(["mark-as-local"])


if __name__ == "__main__":
    run()