"""Link doctor profiles to doctor user accounts.

Revision ID: 0009_doctor_user_link
Revises: 0008_appointment_idempotency
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0009_doctor_user_link"
down_revision: Union[str, None] = "0008_appointment_idempotency"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("doctors") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True))
        batch_op.create_foreign_key(
            "fk_doctors_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_index("ix_doctors_user_id", "doctors", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_doctors_user_id", table_name="doctors")
    with op.batch_alter_table("doctors") as batch_op:
        batch_op.drop_constraint("fk_doctors_user_id_users", type_="foreignkey")
        batch_op.drop_column("user_id")
