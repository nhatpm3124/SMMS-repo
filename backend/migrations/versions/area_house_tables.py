"""Add Area and House tables

Revision ID: area_house_tables
Revises: create_root_user
Create Date: 2025-05-11 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'area_house_tables'
down_revision = 'create_root_user'  # Adjust this to match your last migration
branch_labels = None
depends_on = None

def upgrade():
    # Create Area table
    op.create_table('area',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create House table
    op.create_table('house',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('area_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['area_id'], ['area.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Update existing users to be more specific with area and house
    # This assumes users table already has these columns
    # If not, add them first
    op.execute("""
    ALTER TABLE "user" 
    ALTER COLUMN area TYPE VARCHAR(100),
    ALTER COLUMN house TYPE VARCHAR(100)
    """)

def downgrade():
    # Drop the tables in reverse order
    op.drop_table('house')
    op.drop_table('area')
