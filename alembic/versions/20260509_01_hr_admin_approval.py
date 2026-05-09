"""hr admin approval flag

Revision ID: 20260509_01
Revises: 20260508_02
Create Date: 2026-05-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260509_01"
down_revision: Union[str, None] = "20260508_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("hr_approved", sa.Boolean(), nullable=True))
    op.execute(sa.text("UPDATE users SET hr_approved = true"))
    op.alter_column("users", "hr_approved", nullable=False, server_default=sa.text("false"))


def downgrade() -> None:
    op.drop_column("users", "hr_approved")
