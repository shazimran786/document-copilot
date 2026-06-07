"""One-off schema verification against the linked Supabase database."""

from sqlalchemy import create_engine, inspect, text

from app.config import settings

EXPECTED_TABLES = [
    "chat_messages",
    "chat_threads",
    "document_chunks",
    "message_citations",
    "source_documents",
    "users",
]


def main() -> None:
    url = settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(url)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    missing = [name for name in EXPECTED_TABLES if name not in tables]
    print(f"tables missing: {missing or 'none'}")

    with engine.connect() as conn:
        vector = conn.execute(
            text("select extname from pg_extension where extname = 'vector'")
        ).scalar()
        chunk_cols = [
            row[0]
            for row in conn.execute(
                text(
                    """
                    select column_name
                    from information_schema.columns
                    where table_name = 'document_chunks'
                      and column_name in ('embedding', 'search_vector')
                    order by column_name
                    """
                )
            )
        ]
        indexes = [
            row[0]
            for row in conn.execute(
                text(
                    """
                    select indexname
                    from pg_indexes
                    where tablename = 'document_chunks'
                      and indexname like 'document_chunks_%'
                    order by indexname
                    """
                )
            )
        ]
        rls = list(
            conn.execute(
                text(
                    """
                    select tablename, rowsecurity
                    from pg_tables
                    where schemaname = 'public'
                      and tablename = any(:tables)
                    order by tablename
                    """
                ),
                {"tables": EXPECTED_TABLES},
            )
        )

    print(f"vector extension: {vector}")
    print(f"document_chunks columns: {chunk_cols}")
    print(f"document_chunks indexes: {indexes}")
    print(f"rls enabled: {rls}")


if __name__ == "__main__":
    main()
