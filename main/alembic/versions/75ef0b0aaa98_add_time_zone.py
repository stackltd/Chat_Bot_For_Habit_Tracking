"""add time_zone

Revision ID: 75ef0b0aaa98
Revises: 9adb530f77fe
Create Date: 2025-07-08 00:30:31.272728

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "75ef0b0aaa98"
down_revision: Union[str, Sequence[str], None] = "9adb530f77fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("user", sa.Column("time_zone", sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "time_zone")
    # ### end Alembic commands ###
