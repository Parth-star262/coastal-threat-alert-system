from pathlib import Path

import psycopg2

from config import DB_CONFIG


def main():
    migrations_dir = Path(__file__).parent / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        raise RuntimeError("No SQL migrations found")

    with psycopg2.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            for migration in migration_files:
                cursor.execute(migration.read_text(encoding="utf-8"))
        connection.commit()

    print(f"Applied {len(migration_files)} migrations")


if __name__ == "__main__":
    main()
