"""Initial contents

Revision ID: 2f8500392716
Revises: 
Create Date: 2025-04-17 18:58:18.779350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f8500392716'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('files',
                    sa.Column('fileid', sa.Integer, primary_key=True),
                    sa.Column('expname', sa.Text, index=True),
                    sa.Column('ccd', sa.Text, index=True),
                    sa.Column('band', sa.Text),
                    sa.Column('name', sa.Text)
                   )
    op.create_index("files_expname_ccd_index", "files", ["expname", "ccd"], unique=True)

    op.create_table('qa',
                    sa.Column('qaid', sa.Integer, primary_key=True),
                    sa.Column('fileid', sa.Integer, nullable=False, index=True),
                    sa.Column('userid', sa.Integer, nullable=False, index=True),
                    sa.Column('problem', sa.Integer, nullable=False, index=True),
                    sa.Column('x', sa.Integer),
                    sa.Column('y', sa.Integer),
                    sa.Column('detail', sa.Text),
                    sa.Column('timestamp', sa.Text, nullable=False,
                              server_default=sa.sql.functions.current_timestamp())
                   )

    op.create_table('submissions',
                    sa.Column('userid', sa.Integer, primary_key=True, index=True),
                    sa.Column('total_files', sa.Integer, nullable=False, index=True,
                              default=sa.text("0")),
                    sa.Column('flagged_files', sa.Integer, nullable=False, index=True,
                              default=sa.text("0")),
                   )

    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
