"""extend vacancies with company, location, salary, responsibilities, etc.

Revision ID: 20260510_02
Revises: 20260510_01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260510_02"
down_revision: Union[str, None] = "20260510_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("vacancies", sa.Column("company_name", sa.String(255), nullable=False, server_default=""))
    op.add_column("vacancies", sa.Column("location", sa.String(255), nullable=False, server_default=""))
    op.add_column(
        "vacancies",
        sa.Column("employment_type", sa.String(32), nullable=False, server_default="full_time"),
    )
    op.add_column("vacancies", sa.Column("work_mode", sa.String(32), nullable=False, server_default="office"))
    op.add_column("vacancies", sa.Column("salary_from", sa.Integer(), nullable=True))
    op.add_column("vacancies", sa.Column("salary_to", sa.Integer(), nullable=True))
    op.add_column(
        "vacancies",
        sa.Column("salary_currency", sa.String(10), nullable=False, server_default="UZS"),
    )
    op.add_column(
        "vacancies",
        sa.Column("salary_negotiable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column("vacancies", sa.Column("responsibilities", sa.Text(), nullable=False, server_default=""))
    op.add_column("vacancies", sa.Column("requirements", sa.Text(), nullable=False, server_default=""))
    op.add_column("vacancies", sa.Column("benefits", sa.Text(), nullable=False, server_default=""))
    op.add_column(
        "vacancies",
        sa.Column("experience_note", sa.String(500), nullable=False, server_default=""),
    )
    op.add_column(
        "vacancies",
        sa.Column("education_note", sa.String(255), nullable=False, server_default=""),
    )
    op.add_column("vacancies", sa.Column("contact_phone", sa.String(50), nullable=True))
    op.add_column("vacancies", sa.Column("expires_at", sa.Date(), nullable=True))

    op.alter_column("vacancies", "company_name", server_default=None)
    op.alter_column("vacancies", "location", server_default=None)
    op.alter_column("vacancies", "employment_type", server_default=None)
    op.alter_column("vacancies", "work_mode", server_default=None)
    op.alter_column("vacancies", "salary_currency", server_default=None)
    op.alter_column("vacancies", "salary_negotiable", server_default=None)
    op.alter_column("vacancies", "responsibilities", server_default=None)
    op.alter_column("vacancies", "requirements", server_default=None)
    op.alter_column("vacancies", "benefits", server_default=None)
    op.alter_column("vacancies", "experience_note", server_default=None)
    op.alter_column("vacancies", "education_note", server_default=None)


def downgrade() -> None:
    op.drop_column("vacancies", "expires_at")
    op.drop_column("vacancies", "contact_phone")
    op.drop_column("vacancies", "education_note")
    op.drop_column("vacancies", "experience_note")
    op.drop_column("vacancies", "benefits")
    op.drop_column("vacancies", "requirements")
    op.drop_column("vacancies", "responsibilities")
    op.drop_column("vacancies", "salary_negotiable")
    op.drop_column("vacancies", "salary_currency")
    op.drop_column("vacancies", "salary_to")
    op.drop_column("vacancies", "salary_from")
    op.drop_column("vacancies", "work_mode")
    op.drop_column("vacancies", "employment_type")
    op.drop_column("vacancies", "location")
    op.drop_column("vacancies", "company_name")
