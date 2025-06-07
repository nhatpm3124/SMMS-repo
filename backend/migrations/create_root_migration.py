"""
Migration script to ensure the root user exists
This migration adds a root user if none exists
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from werkzeug.security import generate_password_hash
import datetime

# Define User table structure for the migration
users = table('users',
    column('id', sa.Integer),
    column('username', sa.String),
    column('email', sa.String),
    column('password_hash', sa.String),
    column('role', sa.String),
    column('status', sa.String),
    column('created_at', sa.DateTime),
    column('updated_at', sa.DateTime)
)

def upgrade():
    # Check if root user already exists
    connection = op.get_bind()
    result = connection.execute(sa.select(users.c.id).where(users.c.username == 'root')).fetchone()
    
    # If no root user, create one
    if not result:
        op.bulk_insert(users,
            [
                {
                    'username': 'root',
                    'email': 'root@admin.com',
                    'password_hash': generate_password_hash('Admin@123'),
                    'role': 'root',
                    'status': 'active',
                    'created_at': datetime.datetime.utcnow(),
                    'updated_at': datetime.datetime.utcnow()
                }
            ]
        )
        print("Root user created successfully by migration.")

def downgrade():
    # Remove the root user on downgrade
    op.execute(
        users.delete().where(users.c.username == 'root')
    )