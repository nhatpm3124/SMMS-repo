from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth import authenticate_user, get_current_user, verify_2fa
from app.services.user import get_all_users, create_new_user, delete_user, update_user, toggle_user_status, bulk_import_users
from app.models.models import AuditLog, User, Area, House, db
from app.utils.cors import cors_preflight
import os
import logging
import traceback
from datetime import datetime

api = Blueprint('api', __name__)

@api.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@api.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    response = jsonify({"status": "ok"})
    return response

@api.route('/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Hello from Flask API!"})

@api.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    token = request.json.get('token', None)
    
    user_data, error = authenticate_user(username, password, token)
    
    if error:
        return jsonify({"error": error}), 401
    
    if user_data.get("requires_2fa"):
        return jsonify({
            "requires_2fa": True,
            "user_id": user_data.get("user_id")
        }), 200
    
    if user_data.get("requires_2fa_setup"):
        return jsonify({
            "requires_2fa_setup": True,
            "user_id": user_data.get("user_id"),
            "secret": user_data.get("secret"),
            "qr_uri": user_data.get("qr_uri"),
            "message": "Root user requires 2FA setup. Scan the QR code with Google Authenticator and verify a token to complete login."
        }), 200
    
    return jsonify({
        "message": "Login successful",
        "token": user_data["token"],
        "user": user_data["user"]
    }), 200

@api.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user = get_current_user()
    
    if not current_user or not (current_user.role in ['admin', 'root']):
        return jsonify({"error": "Admin privileges required"}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if per_page > 10000:
        per_page = 10000
    
    filters = {}
    
    search = request.args.get('search')
    if search:
        filters['search'] = search
    
    role = request.args.get('role')
    if role:
        filters['role'] = role.lower() 
    
    status = request.args.get('status')
    if status:
        filters['status'] = status.lower() 
    
    area = request.args.get('area')
    if area:
        filters['area'] = area
    
    house = request.args.get('house')
    if house:
        filters['house'] = house
    
    logging.info(f"User filters applied: {filters}")
    
    result = get_all_users(page=page, per_page=per_page, filters=filters)
    
    if isinstance(result, dict):
        return jsonify({
            "users": [user.to_dict() for user in result["users"]],
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "per_page": result["per_page"],
                "total_pages": result["total_pages"],
                "has_next": result["has_next"],
                "has_prev": result["has_prev"]
            }
        })
    else:
        return jsonify([user.to_dict() for user in result])

@api.route('/users/mentor-view', methods=['GET'])
@jwt_required()
def get_users_for_mentor():
    """Get users for mentor - allows mentors to access users in their own area/house."""
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
    
    # Allow only mentor, admin, and root roles to access this endpoint
    if not current_user.role in ['mentor', 'admin', 'root']:
        return jsonify({"error": "Unauthorized access"}), 403
    
    # Get mentor's area and house
    mentor_area = current_user.area
    mentor_house = current_user.house
    
    if not mentor_area or not mentor_house:
        return jsonify({"error": "Mentor must have area and house assigned"}), 400
    
    # Default pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if per_page > 10000:
        per_page = 10000
    
    # Set specific filters for users in the same area/house
    filters = {
        'area': mentor_area,
        'house': mentor_house
    }
    
    # Additional filters
    search = request.args.get('search')
    if search:
        filters['search'] = search
    
    role = request.args.get('role')
    if role:
        filters['role'] = role.lower()
    
    status = request.args.get('status')
    if status:
        filters['status'] = status.lower()
    
    result = get_all_users(page=page, per_page=per_page, filters=filters)
    
    if isinstance(result, dict):
        return jsonify({
            "users": [user.to_dict() for user in result["users"]],
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "per_page": result["per_page"],
                "total_pages": result["total_pages"],
                "has_next": result["has_next"],
                "has_prev": result["has_prev"]
            }
        })
    else:
        return jsonify([user.to_dict() for user in result])

@api.route('/users/brosis', methods=['GET'])
@jwt_required()
def get_brosis_for_mentor():
    """Get brosis users for mentor - allows mentors to access brosis users in their own area/house."""
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
    
    # Allow only mentor, admin, and root roles to access this endpoint
    if not current_user.role in ['mentor', 'admin', 'root']:
        return jsonify({"error": "Unauthorized access"}), 403
    
    # Get mentor's area and house
    mentor_area = current_user.area
    mentor_house = current_user.house
    
    if not mentor_area or not mentor_house:
        return jsonify({"error": "Mentor must have area and house assigned"}), 400
    
    # Default pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if per_page > 10000:
        per_page = 10000
    
    # Set specific filters for brosis users in the same area/house
    filters = {
        'role': 'brosis',
        'area': mentor_area,
        'house': mentor_house
    }
    
    # Additional filters
    status = request.args.get('status')
    if status:
        filters['status'] = status.lower()
    
    result = get_all_users(page=page, per_page=per_page, filters=filters)
    
    if isinstance(result, dict):
        return jsonify({
            "users": [user.to_dict() for user in result["users"]],
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "per_page": result["per_page"],
                "total_pages": result["total_pages"],
                "has_next": result["has_next"],
                "has_prev": result["has_prev"]
            }
        })
    else:
        return jsonify([user.to_dict() for user in result])

@api.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    try:
        current_user = get_current_user()
        print(f"Current user: {current_user}")
        
        if not current_user or not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        data = request.json
        print(f"Received data: {data}")
        
        if not data or not all(k in data for k in ('username', 'email')):
            return jsonify({"error": "Missing required fields"}), 400
            
        if data.get('role', '').lower() == 'brosis' and 'studentId' not in data:
            return jsonify({"error": "Student ID is required for BroSis users"}), 400
    except Exception as e:
        import traceback
        print(f"Exception in create_user: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    
    user, error = create_new_user(
        username=data['username'],
        email=data['email'],
        password=data.get('password'), 
        fullName=data.get('fullName'),
        phone=data.get('phone'),
        area=data.get('area'),
        house=data.get('house'),
        role=data.get('role', 'user'),
        status=data.get('status', 'active'),
        student_id=data.get('studentId')  
    )
    
    if error:
        return jsonify({"error": error}), 400
    
    user_agent = request.headers.get('User-Agent', '')
    ip_address = request.remote_addr
    
    AuditLog.log(
        user_id=current_user.id,
        action='create_user_api',
        details=f"Created user {data['username']} via API",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return jsonify(user.to_dict()), 201

@api.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user_endpoint(user_id):
    current_user = get_current_user()
    
    if not current_user or not (current_user.role in ['admin', 'root']):
        return jsonify({"error": "Admin privileges required"}), 403
    
    if str(current_user.id) == str(user_id):
        return jsonify({"error": "You cannot delete your own account"}), 403
        
    target_user = User.query.get(user_id)
    if target_user and target_user.role == 'root':
        return jsonify({"error": "Root user cannot be deleted"}), 403
    
    result, error = delete_user(user_id, current_user.id)
    
    if error:
        return jsonify({"error": error}), 400
    
    return jsonify({"message": "User deleted successfully"}), 200

@api.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user_endpoint(user_id):
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
        
    if not (current_user.role in ['admin', 'root']) and str(current_user.id) != str(user_id):
        return jsonify({"error": "You can only update your own account"}), 403
    
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    user, error = update_user(user_id, current_user.id, **data)
    
    if error:
        return jsonify({"error": error}), 400
    
    return jsonify(user.to_dict()), 200

@api.route('/users/<int:user_id>/toggle-status', methods=['PUT'])
@jwt_required()
def toggle_user_status_endpoint(user_id):
    
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Toggle status endpoint called for user_id={user_id}")
        
        current_user = get_current_user()
        
        if not current_user:
            logger.warning("No current user found in request")
            return jsonify({"error": "Authentication required"}), 401
            
        if not (current_user.role in ['admin', 'root']):
            logger.warning(f"User {current_user.username} with role {current_user.role} attempted to toggle status")
            return jsonify({"error": "Admin privileges required"}), 403
        
        target_user = User.query.get(user_id)
        if not target_user:
            logger.warning(f"Target user {user_id} not found")
            return jsonify({"error": "User not found"}), 404
            
        if target_user.role == 'root' and current_user.role != 'root':
            logger.warning(f"Non-root user {current_user.username} tried to change root user status")
            return jsonify({"error": "Only root users can change root user status"}), 403
        
        user, error = toggle_user_status(user_id, current_user.id)
        
        if error:
            logger.error(f"Error toggling status: {error}")
            return jsonify({"error": error}), 400
        
        return jsonify(user.to_dict()), 200
    except Exception as e:
        logger.error(f"Unexpected error in toggle_status endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api.route('/users/<int:user_id>/setup-2fa', methods=['POST'])
@jwt_required()
def setup_2fa(user_id):
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
        
    if not (current_user.role in ['admin', 'root']) and str(current_user.id) != str(user_id):
        return jsonify({"error": "Not authorized"}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    secret = user.setup_2fa()
    db.session.commit()
    
    uri = user.get_2fa_uri()
    
    AuditLog.log(
        user_id=current_user.id,
        action='setup_2fa',
        details=f"Set up 2FA for user {user.username}",
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    
    return jsonify({
        "secret": secret,
        "qr_uri": uri,
        "message": "2FA setup initialized. Scan the QR code with Google Authenticator and verify a token to complete setup."
    }), 200

@api.route('/users/<int:user_id>/verify-2fa', methods=['POST'])
@jwt_required()
def verify_2fa_endpoint(user_id):
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
        
    if not (current_user.role in ['admin', 'root']) and str(current_user.id) != str(user_id):
        return jsonify({"error": "Not authorized"}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    token = request.json.get('token')
    if not token:
        return jsonify({"error": "Token required"}), 400
    
    if not user.verify_2fa(token):
        return jsonify({"error": "Invalid token"}), 400
    
    user.enable_2fa()
    db.session.commit()
    
    AuditLog.log(
        user_id=current_user.id,
        action='enable_2fa',
        details=f"Enabled 2FA for user {user.username}",
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    
    return jsonify({
        "message": "Two-factor authentication enabled successfully",
        "two_factor_enabled": True
    }), 200

@api.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.json
    if not data or not all(k in data for k in ('current_password', 'new_password')):
        return jsonify({"error": "Missing required fields"}), 400
    
    current_password = data['current_password']
    new_password = data['new_password']
    
    if not current_user.check_password(current_password):
        return jsonify({"error": "Current password is incorrect"}), 400
    
    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400
    
    current_user.set_password(new_password)
    if current_user.role != 'root':
        current_user.password_change_required = False
    
    db.session.commit()
    
    user_agent = request.headers.get('User-Agent', '')
    ip_address = request.remote_addr
    
    AuditLog.log(
        user_id=current_user.id,
        action='change_password',
        details=f"User {current_user.username} changed their password",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return jsonify({
        "message": "Password changed successfully",
        "user": current_user.to_dict()
    }), 200

@api.route('/login/2fa', methods=['POST'])
def verify_2fa_login():
    data = request.json
    
    if not data or not all(k in data for k in ('username', 'password', 'token')):
        return jsonify({"error": "Missing required fields"}), 400
    
    username = data.get('username')
    password = data.get('password')
    token = data.get('token')
    
    user_data, error = authenticate_user(username, password, token)
    
    if error:
        return jsonify({"error": error}), 401
    
    return jsonify({
        "message": "Login successful",
        "token": user_data["token"],
        "user": user_data["user"]
    }), 200

@api.route('/areas', methods=['GET'])
@jwt_required()
def get_areas():
    try:
        current_user = get_current_user()
        if not current_user or not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Permission denied. Only root and admin users can access this resource"}), 403
        
        areas = Area.query.all()
        return jsonify([area.to_dict() for area in areas]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/areas', methods=['POST'])
@jwt_required()
def add_area():
    try:
        current_user = get_current_user()
        if not current_user or current_user.role != 'root':
            return jsonify({"error": "Permission denied. Only root users can add areas"}), 403
        
        data = request.json
        if not data or 'name' not in data:
            return jsonify({"error": "Missing area name"}), 400
        
        existing_area = Area.query.filter_by(name=data['name']).first()
        if existing_area:
            return jsonify({"error": f"Area '{data['name']}' already exists"}), 409
        
        new_area = Area(name=data['name'])
        db.session.add(new_area)
        db.session.commit()
        
        log = AuditLog(
            user_id=current_user.id,
            action=f"Created new area: {data['name']}"
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(new_area.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@api.route('/areas/<int:area_id>', methods=['PUT'])
@jwt_required()
def update_area(area_id):
    """Update an existing area - requires root authentication"""
    try:
        # Check if user is root
        current_user = get_current_user()
        if not current_user or current_user.role != 'root':
            return jsonify({"error": "Permission denied. Only root users can update areas"}), 403
        
        # Get data from request
        data = request.json
        if not data or 'name' not in data:
            return jsonify({"error": "Missing area name"}), 400
        
        # Check if area exists
        area = Area.query.get(area_id)
        if not area:
            return jsonify({"error": f"Area with ID {area_id} does not exist"}), 404
        
        # Check if name is already used by another area
        existing_area = Area.query.filter(Area.name == data['name'], Area.id != area_id).first()
        if existing_area:
            return jsonify({"error": f"Area name '{data['name']}' is already in use"}), 409
        
        # Store old name for logging
        old_name = area.name
        
        # Update area
        area.name = data['name']
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action=f"Updated area: {old_name} -> {data['name']}"
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(area.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@api.route('/areas/<int:area_id>', methods=['DELETE'])
@jwt_required()
def delete_area(area_id):
    """Delete an area - requires root authentication"""
    try:
        # Check if user is root
        current_user = get_current_user()
        if not current_user or current_user.role != 'root':
            return jsonify({"error": "Permission denied. Only root users can delete areas"}), 403
        
        # Check if area exists
        area = Area.query.get(area_id)
        if not area:
            return jsonify({"error": f"Area with ID {area_id} does not exist"}), 404
        
        # Check if area has houses
        houses = House.query.filter_by(area_id=area_id).count()
        if houses > 0:
            return jsonify({"error": f"Cannot delete area '{area.name}' because it has {houses} houses assigned to it"}), 400
        
        # Check if area has users
        users_count = User.query.filter(User.area == area.name).count()
        if users_count > 0:
            return jsonify({"error": f"Cannot delete area '{area.name}' because it has {users_count} users assigned to it"}), 400
        
        # Delete area
        area_name = area.name
        db.session.delete(area)
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action=f"Deleted area: {area_name}"
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({"message": f"Area '{area_name}' deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# House Management Routes
@api.route('/houses', methods=['GET'])
@jwt_required()
def get_houses():
    """Get all houses - requires authentication"""
    try:
        # Check if user is root or admin
        current_user = get_current_user()
        if not current_user or not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Permission denied. Only root and admin users can access this resource"}), 403
        
        # Get all houses
        houses = House.query.all()
        return jsonify([house.to_dict() for house in houses]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/houses', methods=['POST'])
@jwt_required()
def add_house():
    """Add a new house - requires root authentication"""
    try:
        # Check if user is root
        current_user = get_current_user()
        if not current_user or current_user.role != 'root':
            return jsonify({"error": "Permission denied. Only root users can add houses"}), 403
        
        # Get data from request
        data = request.json
        if not data or 'name' not in data or 'areaId' not in data:
            return jsonify({"error": "Missing required fields: name and areaId"}), 400
        
        # Check if area exists
        area = Area.query.get(data['areaId'])
        if not area:
            return jsonify({"error": f"Area with ID {data['areaId']} does not exist"}), 404
        
        # Create new house
        new_house = House(name=data['name'], area_id=data['areaId'])
        db.session.add(new_house)
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action=f"Created new house: {data['name']} in area {area.name}"
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(new_house.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@api.route('/houses/<int:house_id>', methods=['PUT'])
@jwt_required()
def update_house(house_id):
    """Update an existing house - requires root authentication"""
    try:
        # Check if user is root
        current_user = get_current_user()
        if not current_user or current_user.role != 'root':
            return jsonify({"error": "Permission denied. Only root users can update houses"}), 403
        
        # Get data from request
        data = request.json
        if not data or 'name' not in data or 'areaId' not in data:
            return jsonify({"error": "Missing required fields: name and areaId"}), 400
        
        # Check if house exists
        house = House.query.get(house_id)
        if not house:
            return jsonify({"error": f"House with ID {house_id} does not exist"}), 404
        
        # Check if area exists
        area = Area.query.get(data['areaId'])
        if not area:
            return jsonify({"error": f"Area with ID {data['areaId']} does not exist"}), 404
        
        # Store old values for logging
        old_name = house.name
        old_area = Area.query.get(house.area_id).name if house.area_id else "None"
        
        # Update house
        house.name = data['name']
        house.area_id = data['areaId']
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action=f"Updated house: {old_name} (Area: {old_area}) -> {house.name} (Area: {area.name})"
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(house.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@api.route('/houses/<int:house_id>', methods=['DELETE'])
@jwt_required()
def delete_house(house_id):
    """Delete a house - requires root authentication"""
    try:
        # Check if user is root
        current_user = get_current_user()
        if not current_user or current_user.role != 'root':
            return jsonify({"error": "Permission denied. Only root users can delete houses"}), 403
        
        # Check if house exists
        house = House.query.get(house_id)
        if not house:
            return jsonify({"error": f"House with ID {house_id} does not exist"}), 404
        
        # Check if house has users
        area = Area.query.get(house.area_id)
        area_name = area.name if area else "Unknown"
        users_count = User.query.filter_by(house=house.name, area=area_name).count()
        if users_count > 0:
            return jsonify({"error": f"Cannot delete house '{house.name}' because it has {users_count} users assigned to it"}), 400
        
        # Delete house
        house_name = house.name
        db.session.delete(house)
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action=f"Deleted house: {house_name} from area {area_name}"
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({"message": f"House '{house_name}' deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@api.route('/users/import', methods=['POST'])
@jwt_required()
def import_users():
    """Import multiple users from Excel file (protected, admin only) - optimized for large files"""
    try:
        # Check if user is admin
        current_user = get_current_user()
        
        if not current_user or not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
            
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({"error": "Only Excel files (.xlsx or .xls) are supported"}), 400
        
        # Check file size - improved error message for large files
        MAX_FILE_SIZE_MB = 10  # 10 MB limit
        file_size_mb = 0
        
        # Get file size without reading entire file into memory
        file.seek(0, os.SEEK_END)
        file_size_bytes = file.tell()
        file_size_mb = file_size_bytes / (1024 * 1024)
        file.seek(0)  # Reset file pointer to beginning
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            return jsonify({
                "error": f"File too large. Maximum size is {MAX_FILE_SIZE_MB} MB, but received {file_size_mb:.2f} MB",
                "success": 0,
                "error_count": 1
            }), 400
        
        # Process file data - read in chunks for efficiency
        file_data = file.read()
        
        # Log start of import operation
        logger = logging.getLogger(__name__)
        logger.info(f"Starting import of Excel file: {file.filename}, size: {file_size_mb:.2f} MB")
        
        # Check for additional import options from frontend
        auto_generate_username = request.form.get('auto_generate_username') == 'true'
        username_not_required = request.form.get('username_not_required') == 'true'
        
        # Get role from request (for student imports)
        role = request.form.get('role', '').lower()
        
        # Process the file with options
        result = bulk_import_users(
            file_data, 
            current_user.id, 
            auto_generate_username=auto_generate_username,
            username_not_required=username_not_required,
            role=role
        )
        
        # Log the import action in audit log
        AuditLog.log(
            user_id=current_user.id,
            action='import_users',
            details=f"Imported users from Excel: {result['success']} successful, {result['error']} failed, file: {file.filename}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        # Log completion
        logger.info(f"Completed import: {result['success']} successful, {result['error']} failed")
        
        # Return result with appropriate status code
        if result['success'] == 0 and result['error'] > 0:
            return jsonify(result), 400
        else:
            return jsonify(result), 200
            
    except Exception as e:
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error importing users: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api.route('/areas-houses', methods=['GET'])
@jwt_required()
def get_areas_houses():
    """Get all areas with their corresponding houses (protected)"""
    try:
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
            
        # Get all areas
        areas = Area.query.all()
        houses = House.query.all()
        
        # Create a structure that maps areas to their houses
        result = {}
        for area in areas:
            area_houses = [h.name for h in houses if h.area_id == area.id]
            result[area.name] = area_houses
            
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        print(f"Error getting areas and houses: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500
        
@api.route('/users/bulk/delete', methods=['POST'])
@jwt_required()
def bulk_delete_users_endpoint():
    """Delete multiple users at once (protected, admin only)"""
    try:
        # Check if user is admin
        current_user = get_current_user()
        
        if not current_user or not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Get request data
        data = request.json
        if not data or 'mode' not in data:
            return jsonify({"error": "Missing required fields: mode"}), 400
            
        mode = data.get('mode')
        if mode not in ['all', 'selected']:
            return jsonify({"error": "Invalid mode. Must be 'all' or 'selected'"}), 400
            
        # For 'selected' mode, userIds is required
        user_ids = data.get('userIds', [])
        if mode == 'selected' and not user_ids:
            return jsonify({"error": "Selected mode requires userIds"}), 400
        
        # Import the bulk operations module
        from app.services.bulk_user_operations import bulk_delete_users
        from app.models.models import AuditLog
        
        # Add explicit security log entry for this operation
        AuditLog.log(
            user_id=current_user.id,
            action='bulk_delete_security',
            details=f"Bulk delete operation initiated with mode={mode}. Root users are protected.",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        # Perform bulk delete with root users always excluded
        result = bulk_delete_users(mode, user_ids, current_user.id)
        
        if 'error' in result:
            return jsonify({"error": result['error']}), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        print(f"Error in bulk delete: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api.route('/users/bulk/status', methods=['POST'])
@jwt_required()
def bulk_change_status_endpoint():
    """Change status for multiple users at once (protected, admin only)"""
    try:
        # Check if user is admin
        current_user = get_current_user()
        
        if not current_user or not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Get request data
        data = request.json
        if not data or 'mode' not in data or 'action' not in data:
            return jsonify({"error": "Missing required fields: mode and action"}), 400
            
        mode = data.get('mode')
        action = data.get('action')
        
        if mode not in ['all', 'selected']:
            return jsonify({"error": "Invalid mode. Must be 'all' or 'selected'"}), 400
            
        if action not in ['activate', 'deactivate']:
            return jsonify({"error": "Invalid action. Must be 'activate' or 'deactivate'"}), 400
            
        # For 'selected' mode, userIds is required
        user_ids = data.get('userIds', [])
        if mode == 'selected' and not user_ids:
            return jsonify({"error": "Selected mode requires userIds"}), 400
        
        # Import the bulk operations module
        from app.services.bulk_user_operations import bulk_change_status
        from app.models.models import AuditLog
        
        # Add explicit security log entry for this operation
        AuditLog.log(
            user_id=current_user.id,
            action='bulk_status_change_security',
            details=f"Bulk status change operation initiated with mode={mode}, action={action}. Root users are protected.",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        # Perform bulk status change with root users always excluded
        result = bulk_change_status(mode, user_ids, action, current_user.id)
        
        if 'error' in result:
            return jsonify({"error": result['error']}), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        print(f"Error in bulk status change: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api.route('/users/export', methods=['GET'])
@jwt_required()
def export_users():
    """Export users to Excel or CSV format (protected, admin only)"""
    try:
        # Check if user is admin
        current_user = get_current_user()
        
        if not current_user or not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Get export parameters from query string
        mode = request.args.get('mode', 'all')
        if mode not in ['all', 'selected']:
            return jsonify({"error": "Invalid mode. Must be 'all' or 'selected'"}), 400
            
        format = request.args.get('format', 'excel')
        if format not in ['excel', 'csv']:
            return jsonify({"error": "Invalid format. Must be 'excel' or 'csv'"}), 400
            
        # Parse user IDs for selected mode
        user_ids = []
        if mode == 'selected':
            user_ids_str = request.args.get('userIds')
            if not user_ids_str:
                return jsonify({"error": "User IDs required for selected mode"}), 400
            try:
                user_ids = [int(id) for id in user_ids_str.split(',')]
            except ValueError:
                return jsonify({"error": "Invalid user IDs format"}), 400
        
        # Import export service
        from app.services.export import generate_export_file
        
        # Generate the export file
        result = generate_export_file(mode, format, user_ids)
        
        # Log the export action
        details = f"Exported {mode} users to {format} format"
        if mode == 'selected':
            details += f" ({len(user_ids)} users)"
            
        AuditLog.log(
            user_id=current_user.id,
            action='export_users',
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        # Return file download response
        return send_file(
            result['file_obj'],
            mimetype=result['mimetype'],
            as_attachment=True,
            download_name=result['filename']
        )
        
    except Exception as e:
        import traceback
        print(f"Error exporting users: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api.route('/users/<int:user_id>/reset-password', methods=['POST'])
@jwt_required()
def reset_user_password(user_id):
    """Reset a user's password to their username (protected, admin only)"""
    try:
        # Check if user is admin
        current_user = get_current_user()
        
        if not current_user or not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Get the target user
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({"error": "User not found"}), 404
            
        # Prevent resetting root user password by non-root users
        if target_user.role == 'root' and current_user.role != 'root':
            return jsonify({"error": "Only root users can reset root user passwords"}), 403
            
        # Reset password to username
        target_user.set_password(target_user.username)
        db.session.commit()
        
        # Log the password reset
        AuditLog.log(
            user_id=current_user.id,
            action='reset_password',
            details=f"Reset password for user {target_user.username}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        return jsonify({
            "message": f"Password reset successful for user {target_user.username}",
            "user": target_user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Error resetting password: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api.route('/users/bulk/reset-password', methods=['POST'])
@jwt_required()
def bulk_reset_passwords_endpoint():
    """Reset passwords for multiple users at once (protected, admin only)"""
    try:
        # Check if user is admin
        current_user = get_current_user()
        
        if not current_user or not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Get request data
        data = request.json
        if not data or 'mode' not in data:
            return jsonify({"error": "Missing required fields: mode"}), 400
            
        mode = data.get('mode')
        if mode not in ['all', 'selected']:
            return jsonify({"error": "Invalid mode. Must be 'all' or 'selected'"}), 400
            
        # For 'selected' mode, userIds is required
        user_ids = data.get('userIds', [])
        if mode == 'selected' and not user_ids:
            return jsonify({"error": "Selected mode requires userIds"}), 400
        
        # Import the bulk operations module
        from app.services.bulk_reset_passwords import bulk_reset_passwords
        
        # Log the bulk password reset request
        AuditLog.log(
            user_id=current_user.id,
            action='bulk_reset_passwords_security',
            details=f"Bulk password reset operation initiated with mode={mode}. Root users are protected.",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        # Perform bulk password reset with root users always excluded
        result = bulk_reset_passwords(mode, user_ids, current_user.id)
        
        if 'error' in result:
            return jsonify({"error": result['error']}), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        print(f"Error in bulk password reset: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Route bị vô hiệu hóa - sử dụng student_routes.py thay thế
# @api.route('/students', methods=['GET'])
@jwt_required()
def get_students_mock():
    """GET /students route bị vô hiệu hóa - endpoint trong student_routes.py được sử dụng thay thế"""
    try:
        # Check if user is authenticated
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Get filter parameters from query string
        filters = {}
        
        # Search term filter
        search = request.args.get('search')
        if search:
            filters['search'] = search
        
        # Status filter
        status = request.args.get('status')
        if status:
            filters['status'] = status
            
        # Matched filter
        matched = request.args.get('matched')
        if matched:
            filters['matched'] = matched
        
        # Area filter - apply area restriction for non-root users
        if current_user.role != 'root':
            # Non-root users can only see students from their area
            filters['area'] = current_user.area
            print(f"Area restriction applied for {current_user.username}: {current_user.area}")
        else:
            # Root users can filter by area
            area = request.args.get('area')
            if area:
                filters['area'] = area
        
        # House filter
        house = request.args.get('house')
        if house:
            filters['house'] = house
        
        # Log the filters for debugging
        print(f"Student filters applied: {filters}")
        
        # Create mock student data
        mock_students = [
            {
                'id': 1,
                'studentId': 'ST001',
                'fullName': 'Nguyễn Văn A',
                'email': 'nguyenvana@gmail.com',
                'phone': '0901234567',
                'area': 'Khu A',
                'house': 'Nhà A1',
                'areaId': 1,
                'houseId': 1,
                'status': 'active',
                'matched': True,
                'userId': 101,
                'userFullName': 'Trần Thị Mentor',
                'registrationDate': '2023-09-01',
                'notes': 'Sinh viên năm nhất ngành CNTT'
            },
            {
                'id': 2,
                'studentId': 'ST002',
                'fullName': 'Trần Thị B',
                'email': 'tranthib@gmail.com',
                'phone': '0901234568',
                'area': 'Khu B',
                'house': 'Nhà B2',
                'areaId': 2,
                'houseId': 4,
                'status': 'active',
                'matched': False,
                'registrationDate': '2023-09-02',
                'notes': 'Sinh viên năm nhất ngành Kinh tế'
            },
            {
                'id': 3,
                'studentId': 'ST003',
                'fullName': 'Lê Văn C',
                'email': 'levanc@gmail.com',
                'phone': '0901234569',
                'area': 'Khu A',
                'house': 'Nhà A2',
                'areaId': 1,
                'houseId': 2,
                'status': 'inactive',
                'matched': False,
                'registrationDate': '2023-09-03'
            },
            {
                'id': 4,
                'studentId': 'ST004',
                'fullName': 'Phạm Thị D',
                'email': 'phamthid@gmail.com',
                'area': 'Khu C',
                'house': 'Nhà C1',
                'areaId': 3,
                'houseId': 5,
                'status': 'active',
                'matched': True,
                'userId': 102,
                'userFullName': 'Lê Văn Brosis',
                'registrationDate': '2023-09-04'
            }
        ]
        
        # Apply filter for area
        filtered_students = mock_students
        if 'area' in filters and filters['area'] != 'all':
            filtered_students = [s for s in filtered_students if s['area'] == filters['area']]
            
        # Apply filter for house
        if 'house' in filters and filters['house'] != 'all':
            filtered_students = [s for s in filtered_students if s['house'] == filters['house']]
            
        # Apply filter for status
        if 'status' in filters and filters['status'] != 'all':
            filtered_students = [s for s in filtered_students if s['status'] == filters['status']]
            
        # Apply filter for matched
        if 'matched' in filters and filters['matched'] != 'all':
            matched_value = filters['matched'].lower() == 'true'
            filtered_students = [s for s in filtered_students if s['matched'] == matched_value]
            
        # Apply search filter
        if 'search' in filters and filters['search']:
            search_term = filters['search'].lower()
            filtered_students = [
                s for s in filtered_students if 
                search_term in s['fullName'].lower() or 
                search_term in s['studentId'].lower() or 
                search_term in s['email'].lower()
            ]
        
        # Get pagination parameters from query string
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Calculate pagination
        total = len(filtered_students)
        total_pages = (total + per_page - 1) // per_page  # Ceiling division
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total)
        current_page_students = filtered_students[start_idx:end_idx]
        
        return jsonify({
            "students": current_page_students,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        })
        
    except Exception as e:
        print(f"Error fetching students: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api.route('/students', methods=['POST'])
@jwt_required()
def create_student():
    """Create a new student (protected, admin only)"""
    try:
        # Check if user is authenticated and authorized
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
            
        if not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Get student data from request
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # If current user is not root, enforce area restriction
        if current_user.role != 'root' and current_user.area:
            # Ensure student inherits admin's area
            data['area'] = current_user.area
            print(f"Setting student area to admin's area: {current_user.area}")
        
        # Mock student creation (would save to database in real implementation)
        new_student = {
            'id': 5,  # In a real implementation, this would be generated by the database
            'studentId': data.get('studentId', ''),
            'fullName': data.get('fullName', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone'),
            'area': data.get('area'),
            'house': data.get('house'),
            'areaId': data.get('areaId'),
            'houseId': data.get('houseId'),
            'status': data.get('status', 'active'),
            'matched': False,
            'registrationDate': datetime.utcnow().strftime('%Y-%m-%d')
        }
        
        # Log creation
        AuditLog.log(
            user_id=current_user.id,
            action='create_student',
            details=f"Created student {data.get('studentId')}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        return jsonify(new_student), 201
        
    except Exception as e:
        print(f"Error creating student: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500