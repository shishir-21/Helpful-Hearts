"""Add patient-controlled medical record doctor access.

Revision ID: 0012_medical_record_access
Revises: 0011_medical_record_uploads
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0012_medical_record_access"
down_revision: Union[str, None] = "0011_medical_record_uploads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "medical_record_access",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("medical_record_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("doctor_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("granted_by", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["medical_record_id"], ["medical_records.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("medical_record_id", "doctor_id", name="uq_medical_record_doctor_access"),
    )
    op.create_index("ix_medical_record_access_medical_record_id", "medical_record_access", ["medical_record_id"])
    op.create_index("ix_medical_record_access_doctor_id", "medical_record_access", ["doctor_id"])


def downgrade() -> None:
    op.drop_index("ix_medical_record_access_doctor_id", table_name="medical_record_access")
    op.drop_index("ix_medical_record_access_medical_record_id", table_name="medical_record_access")
    op.drop_table("medical_record_access")
