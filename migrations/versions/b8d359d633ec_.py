"""empty message

Revision ID: b8d359d633ec
Revises: 3652f00cd373
Create Date: 2023-02-24 16:14:05.712331

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8d359d633ec'
down_revision = '3652f00cd373'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('payslips', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.Enum('Approved', 'Declined', 'Pending', name='status_types'), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('payslips', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###
