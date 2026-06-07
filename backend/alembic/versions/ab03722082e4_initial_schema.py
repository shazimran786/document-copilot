"""initial schema

Revision ID: ab03722082e4
Revises:
Create Date: 2026-06-06 18:00:38.447053

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ab03722082e4"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSIONS = 1536

message_role_enum = postgresql.ENUM(
    "user",
    "assistant",
    name="message_role",
    create_type=False,
)


def upgrade() -> None:
    op.execute("create extension if not exists vector")

    message_role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "source_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("filing_type", sa.String(length=16), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("accession_number", sa.String(length=32), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("markdown_content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "accession_number", name="uq_source_documents_accession"
        ),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("stable_chunk_id", sa.String(length=128), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("page_label", sa.String(length=64), nullable=True),
        sa.Column("section_label", sa.String(length=255), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column(
            "chunk_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["source_documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunks_document_index",
        ),
        sa.UniqueConstraint(
            "stable_chunk_id", name="uq_document_chunks_stable_id"
        ),
    )
    op.create_index(
        "ix_document_chunks_document_id",
        "document_chunks",
        ["document_id"],
        unique=False,
    )

    op.execute(
        """
        alter table document_chunks
        add column search_vector tsvector
        generated always as (
            to_tsvector('english', coalesce(chunk_text, ''))
        ) stored
        """
    )
    op.execute(
        """
        create index document_chunks_embedding_hnsw_idx
        on document_chunks
        using hnsw (embedding vector_cosine_ops)
        """
    )
    op.execute(
        """
        create index document_chunks_search_vector_gin_idx
        on document_chunks
        using gin (search_vector)
        """
    )
    op.execute(
        """
        create index document_chunks_metadata_gin_idx
        on document_chunks
        using gin (chunk_metadata)
        """
    )

    op.create_table(
        "chat_threads",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "title",
            sa.String(length=255),
            server_default="New chat",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chat_threads_user_id", "chat_threads", ["user_id"], unique=False
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("thread_id", sa.UUID(), nullable=False),
        sa.Column("role", message_role_enum, nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column(
            "message_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["thread_id"], ["chat_threads.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "thread_id",
            "sequence_number",
            name="uq_chat_messages_thread_sequence",
        ),
    )
    op.create_index(
        "ix_chat_messages_thread_id",
        "chat_messages",
        ["thread_id"],
        unique=False,
    )

    op.create_table(
        "message_citations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("chunk_id", sa.UUID(), nullable=False),
        sa.Column("claim_index", sa.Integer(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column(
            "citation_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"], ["document_chunks.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["message_id"], ["chat_messages.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_message_citations_chunk_id",
        "message_citations",
        ["chunk_id"],
        unique=False,
    )
    op.create_index(
        "ix_message_citations_message_id",
        "message_citations",
        ["message_id"],
        unique=False,
    )

    op.execute(
        """
        create or replace function public.handle_new_user()
        returns trigger
        language plpgsql
        security definer
        set search_path = ''
        as $$
        begin
          insert into public.users (id, email)
          values (new.id, new.email);
          return new;
        end;
        $$;
        """
    )
    op.execute(
        """
        create trigger on_auth_user_created
        after insert on auth.users
        for each row execute function public.handle_new_user();
        """
    )

    for table in (
        "users",
        "source_documents",
        "document_chunks",
        "chat_threads",
        "chat_messages",
        "message_citations",
    ):
        op.execute(f"alter table {table} enable row level security")

    op.execute(
        """
        create policy users_select_own on users
        for select to authenticated
        using (auth.uid() = id)
        """
    )
    op.execute(
        """
        create policy users_update_own on users
        for update to authenticated
        using (auth.uid() = id)
        """
    )
    op.execute(
        """
        create policy source_documents_select_authenticated on source_documents
        for select to authenticated
        using (true)
        """
    )
    op.execute(
        """
        create policy document_chunks_select_authenticated on document_chunks
        for select to authenticated
        using (true)
        """
    )
    op.execute(
        """
        create policy chat_threads_all_own on chat_threads
        for all to authenticated
        using (auth.uid() = user_id)
        with check (auth.uid() = user_id)
        """
    )
    op.execute(
        """
        create policy chat_messages_all_own on chat_messages
        for all to authenticated
        using (
          exists (
            select 1
            from chat_threads t
            where t.id = thread_id and t.user_id = auth.uid()
          )
        )
        with check (
          exists (
            select 1
            from chat_threads t
            where t.id = thread_id and t.user_id = auth.uid()
          )
        )
        """
    )
    op.execute(
        """
        create policy message_citations_all_own on message_citations
        for all to authenticated
        using (
          exists (
            select 1
            from chat_messages m
            join chat_threads t on t.id = m.thread_id
            where m.id = message_id and t.user_id = auth.uid()
          )
        )
        with check (
          exists (
            select 1
            from chat_messages m
            join chat_threads t on t.id = m.thread_id
            where m.id = message_id and t.user_id = auth.uid()
          )
        )
        """
    )


def downgrade() -> None:
    op.execute(
        "drop policy if exists message_citations_all_own on message_citations"
    )
    op.execute("drop policy if exists chat_messages_all_own on chat_messages")
    op.execute("drop policy if exists chat_threads_all_own on chat_threads")
    op.execute(
        "drop policy if exists document_chunks_select_authenticated on document_chunks"
    )
    op.execute(
        "drop policy if exists source_documents_select_authenticated on source_documents"
    )
    op.execute("drop policy if exists users_update_own on users")
    op.execute("drop policy if exists users_select_own on users")

    op.execute(
        "drop trigger if exists on_auth_user_created on auth.users"
    )
    op.execute("drop function if exists public.handle_new_user()")

    op.drop_index("ix_message_citations_message_id", table_name="message_citations")
    op.drop_index("ix_message_citations_chunk_id", table_name="message_citations")
    op.drop_table("message_citations")

    op.drop_index("ix_chat_messages_thread_id", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("ix_chat_threads_user_id", table_name="chat_threads")
    op.drop_table("chat_threads")

    op.execute("drop index if exists document_chunks_metadata_gin_idx")
    op.execute("drop index if exists document_chunks_search_vector_gin_idx")
    op.execute("drop index if exists document_chunks_embedding_hnsw_idx")
    op.execute("alter table document_chunks drop column if exists search_vector")

    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_table("source_documents")
    op.drop_table("users")

    message_role_enum.drop(op.get_bind(), checkfirst=True)
    op.execute("drop extension if exists vector")
