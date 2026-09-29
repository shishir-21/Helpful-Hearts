"""Create doctor and hospital data tables.

Revision ID: 0002_doctor_data
Revises: 0001_create_users
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_doctor_data"
down_revision: Union[str, None] = "0001_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
        sa.CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND longitude IS NOT NULL)",
            name="ck_hospitals_coordinate_pair",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hospitals_name", "hospitals", ["name"])
    op.create_index("ix_hospitals_city", "hospitals", ["city"])

    op.create_table(
        "doctors",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("specialty", sa.String(120), nullable=False),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("years_experience", sa.Integer(), nullable=True),
        sa.Column("languages", sa.String(300), nullable=True),
        sa.Column("public_phone", sa.String(30), nullable=True),
        sa.Column("public_email", sa.String(320), nullable=True),
        sa.Column("booking_instructions", sa.Text(), nullable=True),
        sa.Column("registration_number", sa.String(100), nullable=True),
        sa.Column("registration_council", sa.String(180), nullable=True),
        sa.Column("registration_state", sa.String(100), nullable=True),
        sa.Column("registration_year", sa.Integer(), nullable=True),
        sa.Column("profile_status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("source_name", sa.String(180), nullable=False, server_default="Helpful Hearts demo dataset"),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("years_experience IS NULL OR years_experience >= 0", name="ck_doctors_experience_nonnegative"),
        sa.CheckConstraint("profile_status IN ('draft', 'submitted', 'verified', 'rejected')", name="ck_doctors_profile_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doctors_full_name", "doctors", ["full_name"])
    op.create_index("ix_doctors_specialty", "doctors", ["specialty"])

    op.create_table(
        "doctor_credentials",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("doctor_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("degree", sa.String(180), nullable=False),
        sa.Column("institution", sa.String(180), nullable=True),
        sa.Column("year_awarded", sa.Integer(), nullable=True),
        sa.Column("verification_status", sa.String(24), nullable=False, server_default="unverified"),
        sa.Column("verification_note", sa.Text(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_name", sa.String(180), nullable=False, server_default="Doctor-submitted"),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "verification_status IN ('unverified', 'pending', 'verified', 'rejected')",
            name="ck_doctor_credentials_verification_status",
        ),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doctor_credentials_doctor_id", "doctor_credentials", ["doctor_id"])

    op.create_table(
        "doctor_hospital_affiliations",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("doctor_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("hospital_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("role_title", sa.String(120), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="current"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("source_name", sa.String(180), nullable=False, server_default="Helpful Hearts demo dataset"),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('current', 'former', 'pending')", name="ck_affiliations_status"),
        sa.CheckConstraint("end_date IS NULL OR start_date IS NULL OR end_date >= start_date", name="ck_affiliations_dates"),
        sa.CheckConstraint("status != 'current' OR end_date IS NULL", name="ck_affiliations_current_no_end_date"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doctor_hospital_affiliations_doctor_id", "doctor_hospital_affiliations", ["doctor_id"])
    op.create_index("ix_doctor_hospital_affiliations_hospital_id", "doctor_hospital_affiliations", ["hospital_id"])


def downgrade() -> None:
    op.drop_index("ix_doctor_hospital_affiliations_hospital_id", table_name="doctor_hospital_affiliations")
    op.drop_index("ix_doctor_hospital_affiliations_doctor_id", table_name="doctor_hospital_affiliations")
    op.drop_table("doctor_hospital_affiliations")
    op.drop_index("ix_doctor_credentials_doctor_id", table_name="doctor_credentials")
    op.drop_table("doctor_credentials")
    op.drop_index("ix_doctors_specialty", table_name="doctors")
    op.drop_index("ix_doctors_full_name", table_name="doctors")
    op.drop_table("doctors")
    op.drop_index("ix_hospitals_city", table_name="hospitals")
    op.drop_index("ix_hospitals_name", table_name="hospitals")
    op.drop_table("hospitals")
