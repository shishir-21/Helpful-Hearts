"""Add idempotency keys to appointments.

Revision ID: 0008_appointment_idempotency
Revises: 0007_assistant
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008_appointment_idempotency"
down_revision: Union[str, None] = "0007_assistant"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("appointments", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    op.create_index(
        "ix_appointments_idempotency_key",
        "appointments",
        ["idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_appointments_idempotency_key", table_name="appointments")
    op.drop_column("appointments", "idempotency_key")
