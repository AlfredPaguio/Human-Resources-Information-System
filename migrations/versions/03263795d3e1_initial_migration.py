"""Initial migration

Revision ID: 03263795d3e1
Revises: 
Create Date: 2023-02-20 10:49:01.115044

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '03263795d3e1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('announcements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date_created', sa.Date(), nullable=False),
    sa.Column('announced_by', sa.String(length=500), nullable=False),
    sa.Column('message', sa.String(length=500), nullable=False),
    sa.Column('employee_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['employee_id'], ['employee_info.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('attendance', schema=None) as batch_op:
        batch_op.alter_column('attendance_type',
               existing_type=mysql.ENUM('Present', 'Absent', 'Unavailable', 'Late', 'On_Leave'),
               type_=sa.Enum('Present', 'Absent', 'Late', 'Unavailable', 'On_Leave', name='attendance_types'),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('attendance', schema=None) as batch_op:
        batch_op.alter_column('attendance_type',
               existing_type=sa.Enum('Present', 'Absent', 'Late', 'Unavailable', 'On_Leave', name='attendance_types'),
               type_=mysql.ENUM('Present', 'Absent', 'Unavailable', 'Late', 'On_Leave'),
               existing_nullable=False)

    op.drop_table('announcements')
    # ### end Alembic commands ###