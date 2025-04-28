"""Upgrade userid to bigint

Revision ID: 296d11c9fd94
Revises: 2f8500392716
Create Date: 2025-04-17 23:01:12.639680

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '296d11c9fd94'
down_revision: Union[str, None] = '2f8500392716'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("qa", "userid", type_=sa.BigInteger)
    op.alter_column("submissions", "userid", type_=sa.BigInteger)
    return


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("qa", "userid", type_=sa.Integer)
    op.alter_column("submissions", "userid", type_=sa.Integer)
    return
