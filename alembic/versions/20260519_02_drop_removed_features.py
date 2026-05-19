"""Drop favorites, saved searches, interviews tables (API removed).

Revision ID: 20260519_02
Revises: 20260519_01
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260519_02"
down_revision: Union[str, None] = "20260519_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("interviews")
    op.drop_table("saved_searches")
    op.drop_table("saved_vacancies")


def downgrade() -> None:
    import sqlalchemy as sa

    op.create_table(
        "saved_vacancies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vacancy_id", sa.Integer(), sa.ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("candidate_id", "vacancy_id", name="uq_saved_vacancy"),
    )
    op.create_table(
        "saved_searches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("filters_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "interviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "application_id",
            sa.Integer(),
            sa.ForeignKey("vacancy_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("format", sa.String(32), nullable=False),
        sa.Column("location_or_link", sa.String(500), server_default="", nullable=False),
        sa.Column("notes", sa.Text(), server_default="", nullable=False),
        sa.Column("status", sa.String(32), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
