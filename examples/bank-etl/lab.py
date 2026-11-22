"""Transfer and verify the three synthetic bank tables."""
import argparse
import os
from pathlib import Path

import oracledb
import psycopg

TABLES = {
    "customers": ("customer_id", "customer_name", "city"),
    "accounts": ("account_id", "customer_id", "currency", "balance"),
    "transactions": ("transaction_id", "account_id", "booked_at", "amount", "transaction_type"),
}


def passwords():
    file = Path(__file__).with_name(".env")
    if file.exists():
        for line in file.read_text().splitlines():
            if line.startswith(("BANK_PG_PASSWORD=", "BANK_ORACLE_PASSWORD=")):
                key, value = line.split("=", 1)
                os.environ.setdefault(key, value)
    return os.environ["BANK_PG_PASSWORD"], os.environ["BANK_ORACLE_PASSWORD"]


def merge(cursor, table, columns, rows):
    if not rows:
        return
    key, *fields = columns
    select = ", ".join(f":{index} {column}" for index, column in enumerate(columns, 1))
    updates = ", ".join(f"t.{field} = s.{field}" for field in fields)
    values = ", ".join(f"s.{column}" for column in columns)
    if "booked_at" in columns:
        cursor.setinputsizes(*(oracledb.DB_TYPE_TIMESTAMP if column == "booked_at" else None for column in columns))
    cursor.executemany(
        f"MERGE INTO {table} t USING (SELECT {select} FROM dual) s ON (t.{key} = s.{key}) "
        f"WHEN MATCHED THEN UPDATE SET {updates} "
        f"WHEN NOT MATCHED THEN INSERT ({', '.join(columns)}) VALUES ({values})",
        rows,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "load", "verify"))
    parser.add_argument("--dry-run", action="store_true", help="Verify load and roll back Oracle writes")
    args = parser.parse_args()
    if args.dry_run and args.action != "load":
        parser.error("--dry-run requires load")
    pg_pwd, ora_pwd = passwords()
    oracledb.defaults.fetch_decimals = True
    with psycopg.connect(
        host="127.0.0.1", port=15432, user="bank_source", password=pg_pwd, dbname="bank_source",
        connect_timeout=5,
    ) as source, oracledb.connect(
        user="bank_dwh", password=ora_pwd, dsn="127.0.0.1:11521/FREEPDB1", tcp_connect_timeout=5,
    ) as target, target.cursor() as cursor:
        source.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        matched = True
        print(f"{'TABLE':15} {'PostgreSQL':>10} {'Oracle':>7}  Result")
        for table, columns in TABLES.items():
            query = f"SELECT {', '.join(columns)} FROM {table} ORDER BY {columns[0]}"
            rows = source.execute(query).fetchall()
            if args.action == "load":
                merge(cursor, table, columns, rows)
            cursor.execute(query)
            loaded = cursor.fetchall()
            same = rows == loaded
            matched &= same
            result = "MATCH" if same else "DIFFERENT"
            print(f"{table:15} {len(rows):10} {len(loaded):7}  {result}")

        if args.action != "status" and not matched:
            raise SystemExit("Source and target rows differ.")
        if args.action == "load":
            if args.dry_run:
                target.rollback()
                print("Dry run passed. Oracle writes were rolled back.")
            else:
                target.commit()
                print("Load committed.")


if __name__ == "__main__":
    main()
