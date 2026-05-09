"""fix integer id defaults

Revision ID: 20260508_02
Revises: 20260508_01
Create Date: 2026-05-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260508_02"
down_revision: Union[str, None] = "20260508_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _set_identity_default(table_name: str) -> None:
    op.execute(
        sa.text(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                      AND column_name = 'id'
                      AND data_type IN ('integer', 'bigint')
                ) THEN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_attrdef d
                        JOIN pg_class c ON c.oid = d.adrelid
                        JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = d.adnum
                        WHERE c.relname = '{table_name}'
                          AND a.attname = 'id'
                    ) THEN
                        EXECUTE 'CREATE SEQUENCE IF NOT EXISTS {table_name}_id_seq';
                        EXECUTE 'SELECT setval(''{table_name}_id_seq'', COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1, false)';
                        EXECUTE 'ALTER TABLE {table_name} ALTER COLUMN id SET DEFAULT nextval(''{table_name}_id_seq'')';
                        EXECUTE 'ALTER SEQUENCE {table_name}_id_seq OWNED BY {table_name}.id';
                    END IF;
                END IF;
            END
            $$;
            """
        )
    )


def upgrade() -> None:
    _set_identity_default("users")
    _set_identity_default("email_verification_codes")
    _set_identity_default("password_reset_codes")
    _set_identity_default("refresh_tokens")


def downgrade() -> None:
    for table_name in (
        "refresh_tokens",
        "password_reset_codes",
        "email_verification_codes",
        "users",
    ):
        op.execute(
            sa.text(
                f"""
                ALTER TABLE {table_name}
                ALTER COLUMN id DROP DEFAULT;
                """
            )
        )
