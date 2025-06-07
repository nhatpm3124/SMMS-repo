
from flask_jwt_extended import create_access_token, get_jwt_identity
from flask import request
from app.models.models import User, AuditLog

def authenticate_user(username, password, token=None):
    """
    Authenticate a user
    If 2FA is enabled, a token is required
    """
    if not username or not password:
        return None, "Missing username or password"
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return None, "Invalid username or password"
        
    # Check if user is active
    if user.status != 'active':
        return None, "Account is not active. Please contact an administrator."
    
    # Check if 2FA is required
    # Always require 2FA for root users, otherwise check if it's enabled
    if user.role == 'root' or user.two_factor_enabled:
        # If 2FA isn't set up for a root user, we need to auto-setup
        if user.role == 'root' and not user.two_factor_secret:
            secret = user.setup_2fa()
            # Auto-enable 2FA for root
            user.two_factor_enabled = True
            from app.models.models import db
            db.session.commit()
            # Notify that 2FA setup is required
            return {
                "requires_2fa_setup": True,
                "user_id": str(user.id),
                "secret": secret,
                "qr_uri": user.get_2fa_uri(app_name="FPT System")
            }, None
            
        if not token:
            # Return a special response indicating 2FA is needed
            return {
                "requires_2fa": True,
                "user_id": str(user.id)
            }, None
        
        # Verify the 2FA token
        if not user.verify_2fa(token):
            return None, "Invalid two-factor authentication code"
    
    # Create JWT token with additional claims
    additional_claims = {
        'username': user.username, 
        'is_admin': getattr(user, 'is_admin', False),
        'is_root': getattr(user, 'is_root', False),
        'role': getattr(user, 'role', 'brosis')
    }
    
    access_token = create_access_token(
        identity=str(user.id),  # Convert to string to fix "Subject must be a string" error
        additional_claims=additional_claims
    )
    
    # Log the successful authentication
    user_agent = request.headers.get('User-Agent', '')
    ip = request.remote_addr
    
    AuditLog.log(
        user_id=user.id,
        action='user_login',
        details=f"User {username} logged in",
        ip_address=ip,
        user_agent=user_agent
    )
    
    return {
        "token": access_token,
        "user": user.to_dict()
    }, None

def get_current_user():
    """
    Get the current authenticated user
    """
    try:
        current_user_id = get_jwt_identity()
        # Convert string ID back to integer for database lookup
        user_id = int(current_user_id) if current_user_id is not None else None
        user = User.query.get(user_id)
        return user
    except Exception as e:
        import traceback
        print(f"Exception in get_current_user: {str(e)}")
        print(traceback.format_exc())
        return None
        
def verify_2fa(user, token):
    """
    Verify a 2FA token for a user
    """
    if not user or not token:
        return False
        
    return user.verify_2fa(token)
