#!/usr/bin/env python3
"""
Database schema update utility script.
This script checks and adds any missing columns required by the User model.
"""

import os
import sys
import psycopg2

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.models import db

def column_exists(conn, table, column):
    """Check if a column exists in a table"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{column}'")
    return cursor.fetchone() is not None

def update_schema():
    """Update the database schema with new columns"""
    print("Starting database schema update...")
    
    # Create the Flask app
    app = create_app()
    
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        print("Database tables created.")
        
        # Check for and add necessary columns
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        if db_uri and 'postgresql' in db_uri:
            # Parse PostgreSQL connection parameters
            from urllib.parse import urlparse
            result = urlparse(db_uri)
            dbname = result.path[1:]  # Bỏ dấu / ở đầu
            user = result.username
            password = result.password
            host = result.hostname
            port = result.port or 5432
            
            print(f"Using PostgreSQL database: {dbname} on {host}:{port}")
            
            try:
                conn = psycopg2.connect(
                    dbname=dbname,
                    user=user,
                    password=password,
                    host=host,
                    port=port
                )
                conn.autocommit = True
                
                # Check and add hash_type column
                if not column_exists(conn, 'user', 'hash_type'):
                    print("Adding 'hash_type' column...")
                    cursor = conn.cursor()
                    cursor.execute("ALTER TABLE \"user\" ADD COLUMN hash_type VARCHAR(20) DEFAULT 'sha256'")
                
                # Check and add is_root column
                if not column_exists(conn, 'user', 'is_root'):
                    print("Adding 'is_root' column...")
                    cursor = conn.cursor()
                    cursor.execute("ALTER TABLE \"user\" ADD COLUMN is_root BOOLEAN DEFAULT FALSE")
                
                # Check and add two_factor_secret column
                if not column_exists(conn, 'user', 'two_factor_secret'):
                    print("Adding 'two_factor_secret' column...")
                    cursor = conn.cursor()
                    cursor.execute("ALTER TABLE \"user\" ADD COLUMN two_factor_secret VARCHAR(32)")
                
                # Check and add two_factor_enabled column
                if not column_exists(conn, 'user', 'two_factor_enabled'):
                    print("Adding 'two_factor_enabled' column...")
                    cursor = conn.cursor()
                    cursor.execute("ALTER TABLE \"user\" ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE")
                
                # Check and add role column
                if not column_exists(conn, 'user', 'role'):
                    print("Adding 'role' column...")
                    cursor = conn.cursor()
                    cursor.execute("ALTER TABLE \"user\" ADD COLUMN role VARCHAR(20) DEFAULT 'brosis'")
                    # Update existing users - root users get 'root' role, admins get 'admin' role
                    cursor.execute("UPDATE \"user\" SET role = 'root' WHERE is_root = TRUE")
                    cursor.execute("UPDATE \"user\" SET role = 'admin' WHERE is_admin = TRUE AND is_root = FALSE")
                    cursor.execute("UPDATE \"user\" SET role = 'brosis' WHERE is_admin = FALSE AND is_root = FALSE")
                
                # Check for the audit_log table and create it if it doesn't exist
                cursor = conn.cursor()
                cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'audit_log')")
                if not cursor.fetchone()[0]:
                    print("Creating 'audit_log' table...")
                    cursor.execute("""
                        CREATE TABLE audit_log (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            user_id INTEGER,
                            action VARCHAR(100) NOT NULL,
                            details TEXT,
                            ip_address VARCHAR(50),
                            user_agent VARCHAR(255),
                            FOREIGN KEY (user_id) REFERENCES \"user\" (id)
                        )
                    """)
                
                print("Database schema updated successfully!")
                conn.close()
            except Exception as e:
                print(f"Error updating database schema: {str(e)}")
                return 1
        else:
            print("Database URI not found or not supported. Please check your configuration.")
            return 1
    
    return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(update_schema())
