"""Create local credentials once. Existing credentials are retained."""
import argparse
from getpass import getpass
import json
import os
import re
from pathlib import Path
from secrets import token_urlsafe
from tempfile import NamedTemporaryFile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--gemini", action="store_true", help="Store a Gemini API key from a hidden terminal prompt")
parser.add_argument("--bank-lab", type=Path, metavar="ENV_FILE", help="Import local bank lab credentials")
parser.add_argument("--resend-from", metavar="EMAIL",
                    help="Store a Resend sending key from a hidden prompt and set the sender email")
parser.add_argument("--resend-to", metavar="EMAIL", help="Set the recipient for the bank notification example")
args = parser.parse_args()
if args.resend_to and not args.resend_from:
    parser.error("--resend-to requires --resend-from")

path = Path(os.environ.get("FLOWAI_CONFIG", Path(__file__).with_name("config.local.json"))).resolve()
path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
if path.exists():
    config = json.loads(path.read_text())
else:
    config = {
        "users": {
            role: {"password": token_urlsafe(24), "role": role}
            for role in ("admin", "viewer", "operator")
        },
        "mcp_token": token_urlsafe(32),
    }

changed = "engine_account" not in config
if changed:
    config["engine_account"] = {
        "login": "engine@flowai.local",
        "password": "Fa9" + token_urlsafe(32),
    }

if args.gemini:
    key = getpass("New Gemini API key: ").strip()
    if not key:
        parser.error("Enter a nonempty Gemini API key")
    config["gemini"] = {**config.get("gemini", {}), "api_key": key}
    changed = True

if args.resend_from:
    addresses = {"RESEND_FROM": args.resend_from.strip()}
    if args.resend_to:
        addresses["RESEND_TO"] = args.resend_to.strip()
    if not all(re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+", value) for value in addresses.values()):
        parser.error("Enter valid sender and recipient email addresses")
    key = getpass("Resend API key: ").strip()
    if not key.startswith("re_") or not key[3:] or any(char.isspace() for char in key):
        parser.error("Enter a valid Resend API key")
    config.setdefault("secrets", {}).update(RESEND_API_KEY=key, **addresses)
    changed = True

if args.bank_lab:
    required = {"BANK_PG_PASSWORD", "BANK_ORACLE_PASSWORD"}
    values = {}
    for line in args.bank_lab.read_text().splitlines():
        key, _, value = line.partition("=")
        if key in required and value:
            values[key] = value
    if values.keys() != required:
        parser.error("Both bank lab passwords are required")
    config.setdefault("secrets", {}).update(values)
    changed = True

if changed:
    with NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as file:
        json.dump(config, file, indent=2)
    os.replace(file.name, path)

print(f"Local credentials: {path}")
