"""support threads and messages for admin chat

Revision ID: 20260509_02
Revises: 20260509_01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260509_02"
down_revision: Union[str, None] = "20260509_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    thread_status = postgresql.ENUM("open", "closed", name="supportthreadstatus")
    thread_status.create(bind, checkfirst=True)

    op.create_table(
        "support_threads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("open", "closed", name="supportthreadstatus", create_type=False),
            nullable=False,
            server_default="open",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_support_threads_created_by_id", "support_threads", ["created_by_id"])

    op.create_table(
        "support_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "thread_id",
            sa.Integer(),
            sa.ForeignKey("support_threads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_support_messages_thread_id", "support_messages", ["thread_id"])
    op.create_index("ix_support_messages_sender_id", "support_messages", ["sender_id"])

    # Alembic 20260508_02 dagi kabi id defaultlari
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_attrdef d JOIN pg_class c ON c.oid = d.adrelid JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = d.adnum
                    WHERE c.relname = 'support_threads' AND a.attname = 'id') THEN
                    CREATE SEQUENCE IF NOT EXISTS support_threads_id_seq;
                    SELECT setval('support_threads_id_seq', COALESCE((SELECT MAX(id) FROM support_threads), 0) + 1, false);
                    ALTER TABLE support_threads ALTER COLUMN id SET DEFAULT nextval('support_threads_id_seq');
                    ALTER SEQUENCE support_threads_id_seq OWNED BY support_threads.id;
                END IF;
            END
            $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_attrdef d JOIN pg_class c ON c.oid = d.adrelid JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = d.adnum
                    WHERE c.relname = 'support_messages' AND a.attname = 'id') THEN
                    CREATE SEQUENCE IF NOT EXISTS support_messages_id_seq;
                    SELECT setval('support_messages_id_seq', COALESCE((SELECT MAX(id) FROM support_messages), 0) + 1, false);
                    ALTER TABLE support_messages ALTER COLUMN id SET DEFAULT nextval('support_messages_id_seq');
                    ALTER SEQUENCE support_messages_id_seq OWNED BY support_messages.id;
                END IF;
            END
            $$;
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_support_messages_sender_id", table_name="support_messages")
    op.drop_index("ix_support_messages_thread_id", table_name="support_messages")
    op.drop_table("support_messages")
    op.drop_index("ix_support_threads_created_by_id", table_name="support_threads")
    op.drop_table("support_threads")
    postgresql.ENUM(name="supportthreadstatus").drop(op.get_bind(), checkfirst=True)
