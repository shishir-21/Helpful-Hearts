"""Remove standalone hospital management; keep hospital name on doctor.

Revision ID: 0003_remove_hospital_section
Revises: 0002_doctor_data
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_remove_hospital_section"
down_revision: Union[str, None] = "0002_doctor_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("doctors", sa.Column("hospital_name", sa.String(180), nullable=True))
    # Preserve one existing hospital name per doctor before removing the join tables.
    op.execute(
        """
        UPDATE doctors
        SET hospital_name = (
            SELECT hospitals.name
            FROM doctor_hospital_affiliations
            JOIN hospitals ON hospitals.id = doctor_hospital_affiliations.hospital_id
            WHERE doctor_hospital_affiliations.doctor_id = doctors.id
            ORDER BY CASE WHEN doctor_hospital_affiliations.status = 'current' THEN 0 ELSE 1 END,
                     doctor_hospital_affiliations.created_at DESC
            LIMIT 1
        )
        WHERE EXISTS (
            SELECT 1 FROM doctor_hospital_affiliations
            WHERE doctor_hospital_affiliations.doctor_id = doctors.id
        )
        """
    )
    op.create_index("ix_doctors_hospital_name", "doctors", ["hospital_name"])
    op.drop_index("ix_doctor_hospital_affiliations_hospital_id", table_name="doctor_hospital_affiliations")
    op.drop_index("ix_doctor_hospital_affiliations_doctor_id", table_name="doctor_hospital_affiliations")
    op.drop_table("doctor_hospital_affiliations")
    op.drop_index("ix_hospitals_city", table_name="hospitals")
    op.drop_index("ix_hospitals_name", table_name="hospitals")
    op.drop_table("hospitals")


def downgrade() -> None:
    op.create_table(
        "hospitals",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=False, server_default="India"),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("source_name", sa.String(180), nullable=False, server_default="Helpful Hearts demo dataset"),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hospitals_name", "hospitals", ["name"])
    op.create_index("ix_hospitals_city", "hospitals", ["city"])
    op.drop_index("ix_doctors_hospital_name", table_name="doctors")
    op.drop_column("doctors", "hospital_name")
