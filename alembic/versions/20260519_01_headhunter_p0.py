"""HeadHunter P0: profile, company, vacancy lifecycle, pipeline, notifications, favorites, interviews

Revision ID: 20260519_01
Revises: 20260511_01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260519_01"
down_revision: Union[str, None] = "20260511_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("about", sa.Text(), server_default="", nullable=False),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("industry", sa.String(120), server_default="", nullable=False),
        sa.Column("company_size", sa.String(80), server_default="", nullable=False),
        sa.Column("country", sa.String(120), server_default="", nullable=False),
        sa.Column("city", sa.String(120), server_default="", nullable=False),
        sa.Column("address", sa.String(500), server_default="", nullable=False),
        sa.Column("verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_companies_slug", "companies", ["slug"], unique=True)

    op.create_table(
        "company_members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), server_default="hr", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "user_id", name="uq_company_member"),
    )

    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(100), server_default="", nullable=False),
        sa.Column("last_name", sa.String(100), server_default="", nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("city", sa.String(120), server_default="", nullable=False),
        sa.Column("country", sa.String(120), server_default="", nullable=False),
        sa.Column("telegram", sa.String(120), nullable=True),
        sa.Column("linkedin", sa.String(255), nullable=True),
        sa.Column("github", sa.String(255), nullable=True),
        sa.Column("portfolio_url", sa.String(500), nullable=True),
        sa.Column("about_me", sa.Text(), server_default="", nullable=False),
        sa.Column("expected_salary_from", sa.Integer(), nullable=True),
        sa.Column("expected_salary_to", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(10), server_default="UZS", nullable=False),
        sa.Column("preferred_work_mode", sa.String(20), server_default="any", nullable=False),
        sa.Column("preferred_employment_type", sa.String(50), nullable=True),
        sa.Column("profile_visible", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "candidate_experiences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("position", sa.String(200), nullable=False),
        sa.Column("started_at", sa.Date(), nullable=True),
        sa.Column("ended_at", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
    )
    op.create_table(
        "candidate_educations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution", sa.String(255), nullable=False),
        sa.Column("degree", sa.String(120), server_default="", nullable=False),
        sa.Column("field_of_study", sa.String(200), server_default="", nullable=False),
        sa.Column("started_at", sa.Date(), nullable=True),
        sa.Column("ended_at", sa.Date(), nullable=True),
    )
    op.create_table(
        "candidate_skills",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("level", sa.String(50), server_default="", nullable=False),
    )
    op.create_table(
        "candidate_languages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("language", sa.String(80), nullable=False),
        sa.Column("level", sa.String(50), server_default="", nullable=False),
    )
    op.create_table(
        "candidate_certificates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("issuer", sa.String(255), server_default="", nullable=False),
        sa.Column("issued_at", sa.Date(), nullable=True),
        sa.Column("credential_url", sa.String(500), nullable=True),
    )

    # Vacancy yangi ustunlar
    op.add_column("vacancies", sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True))
    op.add_column("vacancies", sa.Column("status", sa.String(32), server_default="published", nullable=False))
    op.add_column("vacancies", sa.Column("experience_level", sa.String(20), nullable=True))
    op.add_column("vacancies", sa.Column("industry", sa.String(120), server_default="", nullable=False))
    op.add_column("vacancies", sa.Column("skills_required", sa.Text(), server_default="", nullable=False))
    op.add_column("vacancies", sa.Column("headcount", sa.Integer(), server_default="1", nullable=False))
    op.add_column("vacancies", sa.Column("screening_questions", sa.Text(), server_default="", nullable=False))
    op.add_column("vacancies", sa.Column("is_remote_worldwide", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("vacancies", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    op.execute(sa.text("UPDATE vacancies SET status = 'published' WHERE status IS NULL"))

    # Application status: enum -> varchar + pipeline ustunlar
    op.execute(sa.text("ALTER TABLE vacancy_applications ALTER COLUMN status DROP DEFAULT"))
    op.execute(
        sa.text(
            "ALTER TABLE vacancy_applications ALTER COLUMN status TYPE VARCHAR(50) USING status::text"
        )
    )
    op.execute(sa.text("ALTER TABLE vacancy_applications ALTER COLUMN status SET DEFAULT 'applied'"))
    op.execute(sa.text("DROP TYPE IF EXISTS applicationstatus"))
    op.add_column("vacancy_applications", sa.Column("hr_note", sa.Text(), server_default="", nullable=False))
    op.add_column("vacancy_applications", sa.Column("internal_comment", sa.Text(), server_default="", nullable=False))
    op.add_column("vacancy_applications", sa.Column("rating", sa.Integer(), nullable=True))
    op.add_column("vacancy_applications", sa.Column("rejection_reason", sa.String(500), nullable=True))
    op.execute(sa.text("UPDATE vacancy_applications SET status = 'applied' WHERE status = 'pending'"))

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), server_default="", nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("related_entity_type", sa.String(80), nullable=True),
        sa.Column("related_entity_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_table(
        "saved_vacancies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vacancy_id", sa.Integer(), sa.ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("candidate_id", "vacancy_id", name="uq_saved_vacancy"),
    )

    op.create_table(
        "saved_searches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("filters_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "interviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("vacancy_applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("format", sa.String(30), nullable=False),
        sa.Column("location_or_link", sa.String(500), server_default="", nullable=False),
        sa.Column("notes", sa.Text(), server_default="", nullable=False),
        sa.Column("status", sa.String(30), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("interviews")
    op.drop_table("saved_searches")
    op.drop_table("saved_vacancies")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_column("vacancy_applications", "rejection_reason")
    op.drop_column("vacancy_applications", "rating")
    op.drop_column("vacancy_applications", "internal_comment")
    op.drop_column("vacancy_applications", "hr_note")
    op.drop_column("vacancies", "published_at")
    op.drop_column("vacancies", "is_remote_worldwide")
    op.drop_column("vacancies", "screening_questions")
    op.drop_column("vacancies", "headcount")
    op.drop_column("vacancies", "skills_required")
    op.drop_column("vacancies", "industry")
    op.drop_column("vacancies", "experience_level")
    op.drop_column("vacancies", "status")
    op.drop_column("vacancies", "company_id")
    op.drop_table("candidate_certificates")
    op.drop_table("candidate_languages")
    op.drop_table("candidate_skills")
    op.drop_table("candidate_educations")
    op.drop_table("candidate_experiences")
    op.drop_table("candidate_profiles")
    op.drop_table("company_members")
    op.drop_index("ix_companies_slug", table_name="companies")
    op.drop_table("companies")
