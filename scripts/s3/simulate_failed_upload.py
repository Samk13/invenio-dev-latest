from pathlib import Path

import requests
from rich.console import Console

server_url = "https://127.0.0.1:5000"


def run():
    console = Console()
    console.print("[bold red]Simulating a failed upload...[/bold red]")
    # ask user to get an upload token
    upload_token_path = Path(".upload_token")
    if upload_token_path.exists():
        token = upload_token_path.read_text().strip()
    else:
        token = console.input("Please enter your upload token: ")
        upload_token_path.write_text(token)

    console.print(f"[yellow]Creating a draft record ...{token}[/yellow]")
    response = requests.post(
        f"{server_url}/api/records",
        headers={"Authorization": f"Bearer {token}"},
        json={"metadata": {"title": "Test Record"}, "files": {"enabled": True}},
        verify=False,
    )
    if response.status_code != 201:
        console.print(
            f"[bold red]Failed to create draft record: {response.text}[/bold red]"
        )
        return
    json_response = response.json()
    record_id = json_response["id"]
    console.print(f"[green]Draft record created with ID: {record_id}[/green]")
    files_url = json_response["links"]["files"]
    record_url = json_response["links"]["self"]
    console.print("[yellow]Initiating a multipart file upload ...[/yellow]")
    response = requests.post(
        files_url,
        headers={"Authorization": f"Bearer {token}"},
        json=[
            {
                "key": "large_file.bin",
                "transfer": {"type": "M", "part_size": 53687091, "parts": 2},
                "size": 107374182,
            }
        ],
        verify=False,
    )
    if response.status_code != 201:
        console.print(
            f"[bold red]Failed to initiate multipart upload: {response.text}[/bold red]"
        )
        return
    json_response = response.json()
    console.print("JSON Response:", json_response)

    console.print(
        "[yellow]File upload has been created.\n\n"
        "Now please either press any key to continue or let's simulate expired upload:[/yellow]"
    )
    console.print("[blue]   1. kill the server[/blue]")
    console.print("[blue]   2. stop minio[/blue]")
    console.print("[blue]   3. remove data/.minio.sys[/blue]")
    console.print("[blue]   4. restart minio[/blue]")
    console.print("[blue]   5. restart the server[/blue]")

    console.print("[yellow]Then press Enter to continue...[/yellow]")
    input()

    console.print("[yellow]Now trying to delete the upload...[/yellow]")
    response = requests.delete(
        f"{files_url}/large_file.bin",
        headers={"Authorization": f"Bearer {token}"},
        verify=False,
    )
    assert (
        response.status_code >= 200 and response.status_code < 300
    ), f"Failed to delete upload: {response.code} {response.text}"

    console.print("[green]Upload deleted successfully.[/green]")

    console.print("[yellow]Now deleting the draft record...[/yellow]")
    response = requests.delete(
        record_url,
        headers={"Authorization": f"Bearer {token}"},
        verify=False,
    )
    assert (
        response.status_code >= 200 and response.status_code < 300
    ), f"Failed to delete draft record: {response.code} {response.text}"
    console.print("[green]Draft record deleted successfully.[/green]")


if __name__ == "__main__":
    run()
