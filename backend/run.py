import os
import time
import psycopg2
from app import create_app
from app.models.models import db, User

# Create instance directory if it doesn't exist
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance'), exist_ok=True)

app = create_app()

# Helper function to check if a column exists in a table
def column_exists(conn, table, column):
    cursor = conn.cursor()
    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{column}'")
    return cursor.fetchone() is not None

# Helper function to regenerate the database if needed
def rebuild_database():
    """Drop and recreate all tables"""
    with app.app_context():
        print("Rebuilding database...")
        db.drop_all()
        print("Tables dropped.")
        time.sleep(1)  # Small delay to ensure everything is dropped
        db.create_all()
        print("Tables recreated.")
        
        # Create default root user
        root = User.query.filter_by(username='root').first()
        if not root:
            from argon2 import PasswordHasher
            ph = PasswordHasher()
            
            root = User(
                username='root',
                email='root@fpt.com.vn',
                fullName='System Root User',
                phone='+84707279',
                area='FPT HCM',
                house='FPT Tower',
                is_admin=True,
                is_root=True,
                role='root',
                status='active',
                hash_type='argon2id',
                password_hash=ph.hash('FpT@707279-hCMcIty')
            )
            
            # Set up 2FA (optional during setup)
            import pyotp
            root.two_factor_secret = pyotp.random_base32()
            root.two_factor_enabled = False  # Default to disabled for initial setup
            
            db.session.add(root)
            db.session.commit()
            print(f"Root user created successfully: username=root")
            
            # Create admin user for backward compatibility
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin', 
                    email='admin@example.com', 
                    fullName='System Administrator',
                    is_admin=True,
                    is_root=False,
                    role='admin',
                    status='active',
                    hash_type='sha256',
                    phone='+1234567890',
                    area='Main Office',
                    house='HQ Building'
                )
                admin.set_password('admin@123')
                db.session.add(admin)
                db.session.commit()
                print(f"Admin user created successfully: username=admin")
                
        return True
    
    return False

if __name__ == '__main__':
    try:
        # Try normal table creation first
        with app.app_context():
            db.create_all()
            
        # Check if we can access the user table with all fields
        with app.app_context():
            try:
                # Try to query users - this will fail if columns are missing
                users = User.query.all()
                print(f"Database check: Found {len(users)} existing users")
            except Exception as e:
                print(f"Error querying database: {str(e)}")
                print("Will attempt to rebuild database...")
                
                # If querying fails, try to rebuild the database
                if rebuild_database():
                    print("Database rebuilt successfully!")
                else:
                    print("Failed to rebuild database.")
                    
    except Exception as e:
        print(f"Error during database setup: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', os.environ.get('FLASK_PORT', 5001)))
    print(f"Starting server on port {port}")
    
    # Set environment variables for better CORS debugging
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Print CORS configuration info
    print("CORS is configured for the API. Check headers in network requests.")
    print("If you're still facing CORS issues, verify these settings:")
    print("1. Frontend is sending proper headers (OPTIONS preflight)")
    print("2. Backend is responding with correct CORS headers")
    print("3. No network issues between frontend and backend")
    
    app.run(host='0.0.0.0', port=port, debug=True) 
