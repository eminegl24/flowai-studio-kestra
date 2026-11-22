"""Import the checked-in exercises while preserving any existing flows."""
from pathlib import Path
import re

from smoke import request, sign_in, URL

ROOT = Path(__file__).resolve().parent.parent


def main():
    admin = sign_in("admin")
    base = "/api/v1/main/flows"
    examples = ROOT / "examples"
    flows = sorted((examples / "flows").glob("*.yml"))
    flows.append(examples / "bank-etl/connection_check.yml")
    for path in flows:
        source = path.read_text()
        flow_id = re.search(r"^id: ([\w.-]+)$", source, re.MULTILINE)[1]
        namespace = re.search(r"^namespace: ([\w.-]+)$", source, re.MULTILINE)[1]
        name = f"{namespace}/{flow_id}"
        status, _ = request(admin, f"{base}/{name}")
        if status == 200:
            print(f"Existing flow kept: {name}")
            continue
        if status != 404:
            raise SystemExit(f"Could not check {name}: HTTP {status}")
        status, result = request(admin, base, "POST", source.encode(),
                                 {"Origin": URL, "Content-Type": "application/x-yaml"})
        if status not in {200, 201}:
            raise SystemExit(f"Could not import {name}: HTTP {status}: {result}")
        print(f"Imported: {name}")


if __name__ == "__main__":
    main()
