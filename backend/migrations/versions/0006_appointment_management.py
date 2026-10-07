"""Add appointment cancellation and status history.

Revision ID: 0006_appointment_management
Revises: 0005_appointments
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_appointment_management"
down_revision: Union[str, None] = "0005_appointments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_appointments_doctor_starts_at", "appointments", type_="unique")
    op.create_index(
        "uq_appointments_active_doctor_slot",
        "appointments",
        ["doctor_id", "starts_at"],
        unique=True,
        postgresql_where=sa.text("status IN ('confirmed', 'pending')"),
        sqlite_where=sa.text("status IN ('confirmed', 'pending')"),
    )
    op.create_table(
        "appointment_status_history",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("appointment_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("changed_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("previous_status", sa.String(24), nullable=True),
        sa.Column("new_status", sa.String(24), nullable=False),
        sa.Column("event", sa.String(32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_appointment_status_history_appointment_id", "appointment_status_history", ["appointment_id"])


def downgrade() -> None:
    op.drop_index("ix_appointment_status_history_appointment_id", table_name="appointment_status_history")
    op.drop_table("appointment_status_history")
    op.drop_index("uq_appointments_active_doctor_slot", table_name="appointments")
    op.create_unique_constraint("uq_appointments_doctor_starts_at", "appointments", ["doctor_id", "starts_at"])
