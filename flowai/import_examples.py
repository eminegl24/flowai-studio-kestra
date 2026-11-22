"""Import the checked-in exercises while preserving any existing flows."""
from argparse import ArgumentParser
from pathlib import Path
import re

from smoke import request, sign_in, URL

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--bank", action="store_true", help="Include the optional database lab exercises")
    args = parser.parse_args()
    admin = sign_in("admin")
    base = "/api/v1/main/flows"
    examples = ROOT / "examples"
    flows = sorted((examples / "flows").glob("*.yml"))
    if args.bank:
        bank = examples / "bank-etl"
        flows.extend(bank / name for name in (
            "connection_check.yml", "postgres_to_oracle_transactions.yml",
            "postgres_to_oracle_bildirim.yml", "postgres_to_oracle_teshis.yml",
            "teams_notification.yml",
        ))
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
