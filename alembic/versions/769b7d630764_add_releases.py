"""add releases

Revision ID: 769b7d630764
Revises: 296d11c9fd94
Create Date: 2025-05-12 23:04:57.119640

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '769b7d630764'
down_revision: Union[str, None] = '296d11c9fd94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table('releases',
                    sa.Column('release_id', sa.Integer, primary_key=True),
                    sa.Column('name', sa.Text, index=True),
                    sa.Column('description', sa.Text),
                    sa.Column('butler', sa.Text),
                    sa.Column('dataset_type', sa.Text),
                    sa.Column('collection', sa.Text),
                    sa.Column('default_display', sa.Boolean, default=False),
                   )
    op.execute("INSERT INTO releases (release_id, name, butler, dataset_type, collection, default_display) "
               "VALUES (1, 'LSSTCam', 'embargo', 'calexpBinned', 'u/kadrlica/LSSTCam/binCalexp4', true)")

    op.add_column('qa',
                  sa.Column('release',
                            sa.Integer,
                            sa.ForeignKey('releases.release_id'),
                            server_default='1'))

    op.add_column('files',
                  sa.Column('release',
                            sa.Integer,
                            sa.ForeignKey('releases.release_id'),
                            server_default='1'))

def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table('releases')
    op.remove_column('qa', 'release')
    op.remove_column('files', 'release')

