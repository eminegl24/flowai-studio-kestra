"""Generate unique local database passwords without displaying them."""
import os
from pathlib import Path
from secrets import token_hex

path = Path(__file__).with_name(".env")
try:
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as file:
        for name in ("BANK_PG_PASSWORD", "BANK_ORACLE_PASSWORD"):
            print(f"{name}=Lab9a{token_hex(13)}", file=file)
except FileExistsError:
    pass
print(f"Local credentials: {path}")
