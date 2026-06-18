# python scripts/mermaid/uvlock_to_mermaid.py > deps.mmd
import tomllib
from pathlib import Path
from packaging.utils import canonicalize_name

LOCK = Path("uv.lock")

INCLUDE_PREFIXES = ("invenio", "marshmallow", "flask-resources","cookiecutter-invenio-rdm")

data = tomllib.loads(LOCK.read_text())

packages = data["package"]

installed = {
    canonicalize_name(pkg["name"]): pkg["name"]
    for pkg in packages
}

edges = set()

for pkg in packages:
    src = pkg["name"]
    src_key = canonicalize_name(src)

    if not src_key.startswith(INCLUDE_PREFIXES):
        continue

    for dep in pkg.get("dependencies", []):
        dep_name = dep["name"]
        dep_key = canonicalize_name(dep_name)

        if dep_key in installed and dep_key.startswith(INCLUDE_PREFIXES):
            # dep --> package that depends on it
            edges.add((installed[dep_key], src))

def node_id(name: str) -> str:
    return name.replace("-", "_").replace(".", "_")

print("flowchart LR")

for dep, pkg in sorted(edges):
    print(f'  {node_id(dep)}["{dep}"] --> {node_id(pkg)}["{pkg}"]')