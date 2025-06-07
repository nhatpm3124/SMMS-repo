"""Create root user migration

Revision ID: create_root_user
Revises: 
Create Date: 2025-05-10 14:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, Boolean
from datetime import datetime
import argon2

# revision identifiers
revision = 'create_root_user'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Reference to existing user table
    user_table = table('user',
        column('id', Integer),
        column('username', String),
        column('fullName', String),
        column('email', String),
        column('password_hash', String),
        column('hash_type', String),
        column('is_admin', Boolean),
        column('is_root', Boolean),
        column('status', String),
        column('phone', String),
        column('area', String),
        column('house', String),
        column('two_factor_secret', String),
        column('two_factor_enabled', Boolean),
        column('role', String),
    )
    
    # Add columns if they don't exist yet
    try:
        op.add_column('user', sa.Column('is_root', sa.Boolean(), server_default='0', nullable=False))
        op.add_column('user', sa.Column('hash_type', sa.String(length=20), server_default='sha256', nullable=False))
        op.add_column('user', sa.Column('two_factor_secret', sa.String(length=32), nullable=True))
        op.add_column('user', sa.Column('two_factor_enabled', sa.Boolean(), server_default='0', nullable=False))
    except Exception as e:
        print(f"Column addition error (likely already exists): {str(e)}")
        
    # Create audit log table if it doesn't exist
    try:
        op.create_table('audit_log',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('action', sa.String(length=100), nullable=False),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('ip_address', sa.String(length=50), nullable=True),
            sa.Column('user_agent', sa.String(length=255), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception as e:
        print(f"Table creation error (likely already exists): {str(e)}")
    
    # Create root user with argon2id hashed password
    hasher = argon2.PasswordHasher(
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=32,
        salt_len=16,
        encoding='utf-8',
        type=argon2.Type.ID
    )
    password_hash = hasher.hash("FpT@707279-hCMcIty")
    
    # Check if root user already exists
    connection = op.get_bind()
    result = connection.execute("SELECT id FROM user WHERE username = 'root'")
    exists = result.fetchone() is not None
    
    if not exists:
        # Insert root user
        op.execute(
            user_table.insert().values(
                username='root',
                fullName='System Root User',
                email='root@fpt.com.vn',
                password_hash=password_hash,
                hash_type='argon2id',
                is_admin=True,
                is_root=True,
                role='root',
                status='active',
                phone='+84707279',
                area='FPT HCM',
                house='FPT Tower'
            )
        )
        
        print("Root user created successfully.")
    else:
        print("Root user already exists. Skipping creation.")

    # Log the creation in audit table
    audit_table = table('audit_log',
        column('timestamp', sa.DateTime),
        column('user_id', Integer),
        column('action', String),
        column('details', String),
        column('ip_address', String),
    )
    
    # Try to find root user ID
    result = connection.execute("SELECT id FROM user WHERE username = 'root'")
    root_id = result.fetchone()[0]
    
    # Create first audit log entry
    op.execute(
        audit_table.insert().values(
            timestamp=datetime.utcnow(),
            user_id=root_id,
            action='create_root_user',
            details='Root user created via migration',
            ip_address='system'
        )
    )

def downgrade():
    # We don't want to allow deleting the root user via migrations
    pass
