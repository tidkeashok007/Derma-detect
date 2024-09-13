"""alter casereport table

Revision ID: 7658a74f0b5f
Revises: d2a755e47c18
Create Date: 2024-09-03 09:36:17.011310

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '7658a74f0b5f'
down_revision = 'd2a755e47c18'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('case_report', schema=None) as batch_op:
        batch_op.alter_column('doctor_id',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
        batch_op.alter_column('report_description',
               existing_type=mysql.TEXT(),
               nullable=False)
        batch_op.alter_column('files',
               existing_type=mysql.VARCHAR(length=256),
               type_=sa.String(length=255),
               nullable=False)
        batch_op.drop_constraint('case_report_ibfk_3', type_='foreignkey')
        batch_op.drop_constraint('case_report_ibfk_4', type_='foreignkey')
        batch_op.drop_column('appointment_id')
        batch_op.drop_column('user_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('case_report', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('appointment_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('case_report_ibfk_4', 'user', ['user_id'], ['id'])
        batch_op.create_foreign_key('case_report_ibfk_3', 'appointment', ['appointment_id'], ['id'])
        batch_op.alter_column('files',
               existing_type=sa.String(length=255),
               type_=mysql.VARCHAR(length=256),
               nullable=True)
        batch_op.alter_column('report_description',
               existing_type=mysql.TEXT(),
               nullable=True)
        batch_op.alter_column('doctor_id',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=True)

    # ### end Alembic commands ###
