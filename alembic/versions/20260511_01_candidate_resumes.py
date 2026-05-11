"""candidate resumes

Revision ID: 20260511_01
Revises: 20260510_02
Create Date: 2026-05-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260511_01"
down_revision: Union[str, None] = "20260510_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidate_resumes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("candidate_id", name="uq_candidate_resumes_candidate_id"),
    )
    op.create_index("ix_candidate_resumes_candidate_id", "candidate_resumes", ["candidate_id"])

    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_attrdef d JOIN pg_class c ON c.oid = d.adrelid JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = d.adnum
                    WHERE c.relname = 'candidate_resumes' AND a.attname = 'id') THEN
                    CREATE SEQUENCE IF NOT EXISTS candidate_resumes_id_seq;
                    SELECT setval('candidate_resumes_id_seq', COALESCE((SELECT MAX(id) FROM candidate_resumes), 0) + 1, false);
                    ALTER TABLE candidate_resumes ALTER COLUMN id SET DEFAULT nextval('candidate_resumes_id_seq');
                    ALTER SEQUENCE candidate_resumes_id_seq OWNED BY candidate_resumes.id;
                END IF;
            END
            $$;
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_candidate_resumes_candidate_id", table_name="candidate_resumes")
    op.drop_table("candidate_resumes")

