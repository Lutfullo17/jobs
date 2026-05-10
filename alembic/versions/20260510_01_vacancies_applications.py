"""vacancies and vacancy applications (HR <-> candidate chat flow)

Revision ID: 20260510_01
Revises: 20260509_02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260510_01"
down_revision: Union[str, None] = "20260509_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    app_status = postgresql.ENUM("pending", "chat_open", "rejected", name="applicationstatus")
    app_status.create(bind, checkfirst=True)

    op.create_table(
        "vacancies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hr_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_vacancies_hr_id", "vacancies", ["hr_id"])

    op.create_table(
        "vacancy_applications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "vacancy_id",
            sa.Integer(),
            sa.ForeignKey("vacancies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("initial_message", sa.Text(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "chat_open", "rejected", name="applicationstatus", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("vacancy_id", "candidate_id", name="uq_vacancy_candidate"),
    )
    op.create_index("ix_vacancy_applications_vacancy_id", "vacancy_applications", ["vacancy_id"])
    op.create_index("ix_vacancy_applications_candidate_id", "vacancy_applications", ["candidate_id"])

    op.create_table(
        "application_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "application_id",
            sa.Integer(),
            sa.ForeignKey("vacancy_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_application_messages_application_id", "application_messages", ["application_id"])

    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_attrdef d JOIN pg_class c ON c.oid = d.adrelid JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = d.adnum
                    WHERE c.relname = 'vacancies' AND a.attname = 'id') THEN
                    CREATE SEQUENCE IF NOT EXISTS vacancies_id_seq;
                    SELECT setval('vacancies_id_seq', COALESCE((SELECT MAX(id) FROM vacancies), 0) + 1, false);
                    ALTER TABLE vacancies ALTER COLUMN id SET DEFAULT nextval('vacancies_id_seq');
                    ALTER SEQUENCE vacancies_id_seq OWNED BY vacancies.id;
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
                    WHERE c.relname = 'vacancy_applications' AND a.attname = 'id') THEN
                    CREATE SEQUENCE IF NOT EXISTS vacancy_applications_id_seq;
                    SELECT setval('vacancy_applications_id_seq', COALESCE((SELECT MAX(id) FROM vacancy_applications), 0) + 1, false);
                    ALTER TABLE vacancy_applications ALTER COLUMN id SET DEFAULT nextval('vacancy_applications_id_seq');
                    ALTER SEQUENCE vacancy_applications_id_seq OWNED BY vacancy_applications.id;
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
                    WHERE c.relname = 'application_messages' AND a.attname = 'id') THEN
                    CREATE SEQUENCE IF NOT EXISTS application_messages_id_seq;
                    SELECT setval('application_messages_id_seq', COALESCE((SELECT MAX(id) FROM application_messages), 0) + 1, false);
                    ALTER TABLE application_messages ALTER COLUMN id SET DEFAULT nextval('application_messages_id_seq');
                    ALTER SEQUENCE application_messages_id_seq OWNED BY application_messages.id;
                END IF;
            END
            $$;
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_application_messages_application_id", table_name="application_messages")
    op.drop_table("application_messages")
    op.drop_index("ix_vacancy_applications_candidate_id", table_name="vacancy_applications")
    op.drop_index("ix_vacancy_applications_vacancy_id", table_name="vacancy_applications")
    op.drop_table("vacancy_applications")
    op.drop_index("ix_vacancies_hr_id", table_name="vacancies")
    op.drop_table("vacancies")
    postgresql.ENUM(name="applicationstatus").drop(op.get_bind(), checkfirst=True)
