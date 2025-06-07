"""Create Student table migration

Revision ID: 678addea19e5
Revises: current_head
Create Date: 2025-05-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '678addea19e5'
down_revision = None  # Update based on your current migration
branch_labels = None
depends_on = None


def upgrade():
    # Create the student table
    op.create_table('student',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.String(length=20), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('area', sa.String(length=100), nullable=True),
        sa.Column('house', sa.String(length=100), nullable=True),
        sa.Column('area_id', sa.Integer(), nullable=True),
        sa.Column('house_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('matched', sa.Boolean(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('registration_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['area_id'], ['area.id'], ),
        sa.ForeignKeyConstraint(['house_id'], ['house.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id')
    )
    
    # Create indexes for faster lookups
    op.create_index(op.f('ix_student_area'), 'student', ['area'], unique=False)
    op.create_index(op.f('ix_student_house'), 'student', ['house'], unique=False)
    op.create_index(op.f('ix_student_status'), 'student', ['status'], unique=False)
    op.create_index(op.f('ix_student_matched'), 'student', ['matched'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_student_matched'), table_name='student')
    op.drop_index(op.f('ix_student_status'), table_name='student')
    op.drop_index(op.f('ix_student_house'), table_name='student')
    op.drop_index(op.f('ix_student_area'), table_name='student')
    
    # Drop the student table
    op.drop_table('student')
