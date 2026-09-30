"""Add recurring doctor availability rules.

Revision ID: 0004_doctor_availability
Revises: 0003_remove_hospital_section
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_doctor_availability"
down_revision: Union[str, None] = "0003_remove_hospital_section"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "doctor_availability",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("doctor_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("slot_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Asia/Kolkata"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_availability_weekday"),
        sa.CheckConstraint("slot_minutes > 0 AND slot_minutes <= 240", name="ck_availability_slot_minutes"),
        sa.CheckConstraint("end_time > start_time", name="ck_availability_time_range"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doctor_availability_doctor_id", "doctor_availability", ["doctor_id"])


def downgrade() -> None:
    op.drop_index("ix_doctor_availability_doctor_id", table_name="doctor_availability")
    op.drop_table("doctor_availability")
