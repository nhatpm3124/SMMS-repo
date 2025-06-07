#!/usr/bin/env python3
"""
Script to create a custom root user with specific permissions
Usage:
    python create_custom_root.py <username> <email> <password>
"""

import sys
import os
from app import create_app, db
from app.models.models import User
from getpass import getpass

def create_root_user(username, email, password=None):
    """Create a root user with the given credentials"""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User {username} already exists. Updating to root permissions.")
            existing_user.role = 'root'
            db.session.commit()
            return existing_user
        
        # If no password provided, prompt for it securely
        if not password:
            password = getpass("Enter password for root user: ")
            password_confirm = getpass("Confirm password: ")
            if password != password_confirm:
                print("Passwords do not match. Aborting.")
                return None
        
        # Create new root user
        new_root = User(
            username=username,
            email=email,
            role='root',
            status='active'
        )
        new_root.set_password(password)
        
        db.session.add(new_root)
        db.session.commit()
        print(f"Root user {username} created successfully.")
        return new_root

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_custom_root.py <username> <email> [password]")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3] if len(sys.argv) > 3 else None
    
    create_root_user(username, email, password)