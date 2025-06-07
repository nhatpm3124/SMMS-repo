from app.models.models import db, User, AuditLog
from flask import request
import pandas as pd
import io
import logging
import traceback
import time
import random

def get_all_users(page=None, per_page=None, filters=None):
    """
    Get all users with optional pagination and filtering
    
    Filters can include:
    - search: Search term to filter by username, full name, email, etc.
    - role: Filter by user role ('root', 'admin', 'mentor', 'brosis')
    - status: Filter by user status ('active', 'inactive')
    - area: Filter by user area
    - house: Filter by user house
    """
    # Build query with filters
    query = User.query
    
    if filters:
        # Search filter
        if filters.get('search'):
            search_term = f"%{filters.get('search')}%"
            query = query.filter(
                (User.username.ilike(search_term)) |
                (User.fullName.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (User.phone.ilike(search_term)) |
                (User.area.ilike(search_term)) |
                (User.house.ilike(search_term))
            )
        
        # Role filter
        if filters.get('role'):
            query = query.filter(User.role == filters.get('role'))
        
        # Status filter
        if filters.get('status'):
            query = query.filter(User.status == filters.get('status'))
        
        # Area filter
        if filters.get('area'):
            query = query.filter(User.area == filters.get('area'))
        
        # House filter
        if filters.get('house'):
            query = query.filter(User.house == filters.get('house'))
    
    # Apply pagination if requested
    if page is not None and per_page is not None:
        page_zero_indexed = page - 1
        offset = page_zero_indexed * per_page
        
        users = query.order_by(User.id).limit(per_page).offset(offset).all()
        total_count = query.count()
        
        total_pages = (total_count + per_page - 1) // per_page if per_page > 0 else 0
        
        return {
            "users": users,
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    else:
        # Return all users if no pagination requested
        return query.all()

def create_new_user(username, email, password=None, fullName=None, phone=None, 
                area=None, house=None, role='brosis', status='active',
                student_id=None, current_user_id=None, hash_type="sha256"):
    """
    Create a new user
    
    Role can be one of:
    - 'root': Highest level admin (only one allowed in system)
    - 'admin': Administrator with high level permissions
    - 'mentor': Mentor role with specialized permissions
    - 'brosis': Regular user (default role)
    
    If password is not provided, username will be used as the default password
    If username is not provided but role is 'brosis' and both fullName and student_id are provided,
    username will be auto-generated using the pattern: firstName + initials + studentId
    """
    # Auto-generate username for brosis users if not provided but have fullName and student_id
    if not username and role.lower() == 'brosis' and fullName and student_id:
        username = generate_username_from_fullname_and_student_id(fullName, student_id)
        
    # Check if trying to create a root user
    if role.lower() == 'root':
        # Check if a root user already exists
        existing_root = User.query.filter_by(is_root=True).first()
        if existing_root:
            return None, "A root user already exists in the system"
    
    # Check if username or email already exists
    if User.query.filter_by(username=username).first():
        return None, "Username already exists"
    
    if User.query.filter_by(email=email).first():
        return None, "Email already exists"
    
    # Create and save new user
    is_admin = (role.lower() == 'admin')
    is_root = (role.lower() == 'root')
    
    # Set the role value based on input (normalized to lowercase)
    normalized_role = role.lower()
    if normalized_role not in ['root', 'admin', 'mentor', 'brosis']:
        normalized_role = 'brosis'  # Default to brosis if invalid role
    
    if normalized_role == 'root':
        # Root users should use argon2id for enhanced security
        hash_type = "argon2id"
        
    # For admin users, set default house to "FPT + Area" if area is provided but house is not
    if normalized_role == 'admin' and area and not house:
        house = f"FPT {area}"
    
    new_user = User(
        username=username, 
        email=email,
        fullName=fullName,
        phone=phone,
        area=area,
        house=house,
        is_admin=is_admin,  # Keep for backward compatibility
        is_root=is_root,    # Keep for backward compatibility
        role=normalized_role,
        status=status,
        student_id=student_id if normalized_role == 'brosis' else None,  # Only set student_id for BroSis users
        password_change_required=normalized_role != 'root'  # Root users don't need to change their password
    )
    # If password is not provided, use the username as password
    if password is None:
        password = username
        
    new_user.set_password(password, hash_type=hash_type)
    
    db.session.add(new_user)
    db.session.commit()
    
    # Create audit log entry
    if current_user_id:
        user_agent = request.headers.get('User-Agent', '')
        ip = request.remote_addr
        
        AuditLog.log(
            user_id=current_user_id,
            action='create_user',
            details=f"Created new user: {username} (role: {role})",
            ip_address=ip,
            user_agent=user_agent
        )
    
    return new_user, None
    
def update_user(user_id, current_user_id, **kwargs):
    """
    Update an existing user
    """
    user = User.query.get(user_id)
    if not user:
        return None, "User not found"
    
    # Get the current user to check their role
    current_user = User.query.get(current_user_id)
    if not current_user:
        return None, "Current user not found"
    
    # Check if trying to update a root user
    if user.role == 'root' and str(current_user_id) != str(user_id):
        return None, "Root user can only be updated by themselves"
    
    # Check if a non-root user is trying to update an admin user
    if user.role == 'admin' and current_user.role != 'root' and str(current_user_id) != str(user_id):
        return None, "Admin users can only be modified by root users"
    
    # Capture current values for BroSis users to detect changes
    old_house = None
    old_status = None
    
    if user.role == 'brosis':
        old_house = user.house
        old_status = user.status
        
    # Update fields
    for key, value in kwargs.items():
        if key == 'password' and value:
            # Special handling for password
            hash_type = "argon2id" if user.role == 'root' else "sha256"
            user.set_password(value, hash_type=hash_type)
        elif key == 'role':
            # Special handling for role
            if value == 'root' and user.role != 'root':
                # Check if a root user already exists
                existing_root = User.query.filter_by(role='root').first()
                if existing_root:
                    return None, "A root user already exists in the system"
                # Update legacy fields for compatibility
                user.is_root = True
                user.is_admin = True
            elif value in ['admin', 'mentor', 'brosis']:
                # Update legacy fields for compatibility
                user.is_admin = (value == 'admin')
                user.is_root = False
                
            # Set the actual role field
            if value in ['root', 'admin', 'mentor', 'brosis']:
                user.role = value
        elif hasattr(user, key):
            setattr(user, key, value)
    
    # Check if we need to unassign students from this BroSis user
    needs_unassignment = False
    unassignment_reason = ""
    
    # Case 1: Role changed from brosis to something else
    if old_house is not None and 'role' in kwargs and kwargs['role'] != 'brosis':
        needs_unassignment = True
        unassignment_reason = f"BroSis role changed from brosis to {kwargs['role']}"
    # Case 2: BroSis house changed
    elif user.role == 'brosis':
        # Check if house was changed
        if 'house' in kwargs and old_house != user.house:
            needs_unassignment = True
            unassignment_reason = f"BroSis house changed from {old_house} to {user.house}"
        
        # Check if status was changed to inactive
        if 'status' in kwargs and user.status == 'inactive' and old_status != 'inactive':
            needs_unassignment = True
            unassignment_reason = f"BroSis status changed to inactive"
    
    # Unassign students if needed
    if needs_unassignment:
        try:
            # Find all students assigned to this BroSis
            from app.models.student import Student
            students = Student.query.filter_by(user_id=user.id, matched=True).all()
            
            # If students are found, unassign them
            if students:
                unassigned_count = 0
                
                for student in students:
                    student.user_id = None
                    student.matched = False
                    unassigned_count += 1
                
                # Create an audit log entry for this mass unassignment
                try:
                    from app.models.audit import AuditLog
                    from flask import request, has_request_context
                    
                    # Check if we're in a request context to avoid errors
                    if has_request_context():
                        user_agent = request.headers.get('User-Agent', '')
                        ip = request.remote_addr
                    else:
                        user_agent = 'No request context'
                        ip = 'N/A'
                    
                    AuditLog.log(
                        user_id=current_user_id,
                        action='auto_unassign_students',
                        details=f"Auto-unassigned {unassigned_count} students from BroSis {user.username} due to: {unassignment_reason}",
                        ip_address=ip,
                        user_agent=user_agent
                    )
                except Exception as audit_error:
                    print(f"Warning: Could not create audit log for auto-unassignment: {str(audit_error)}")
                    # Continue despite audit log error - the actual unassignment is more important
        except Exception as unassign_error:
            print(f"Error during auto-unassignment for user {user.id}: {str(unassign_error)}")
            # This error shouldn't prevent the user from being updated
            # Just log the error and continue
    
    # Save changes
    db.session.commit()
    
    # Create audit log entry
    user_agent = request.headers.get('User-Agent', '')
    ip = request.remote_addr
    
    AuditLog.log(
        user_id=current_user_id,
        action='update_user',
        details=f"Updated user: {user.username} (ID: {user_id})",
        ip_address=ip,
        user_agent=user_agent
    )
    
    return user, None

def delete_user(user_id, current_user_id):
    """
    Delete a user
    Includes protection against self-deletion and root user deletion
    """
    user = User.query.get(user_id)
    if not user:
        return None, "User not found"
    
    # Prevent deleting self
    if str(user_id) == str(current_user_id):
        return None, "Cannot delete your own account"
    
    # Prevent deleting root user
    if user.role == 'root':
        return None, "Root user cannot be deleted"
    
    # Store username for audit log
    username = user.username
    
    # Delete user
    db.session.delete(user)
    db.session.commit()
    
    # Create audit log entry
    user_agent = request.headers.get('User-Agent', '')
    ip = request.remote_addr
    
    AuditLog.log(
        user_id=current_user_id,
        action='delete_user',
        details=f"Deleted user: {username} (ID: {user_id})",
        ip_address=ip,
        user_agent=user_agent
    )
    
    return True, None

def toggle_user_status(user_id, current_user_id):
    """
    Toggle a user's status between active and inactive
    Includes protection against toggling root user status by non-root users
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Toggling status for user_id={user_id} by current_user_id={current_user_id}")
        
        user = User.query.get(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            return None, "User not found"
            
        # Only root can change root user's status
        current_user = User.query.get(current_user_id)
        if not current_user:
            logger.error(f"Current user not found: {current_user_id}")
            return None, "Current user not found"
            
        logger.info(f"Current user: {current_user.username} (role: {current_user.role})")
        logger.info(f"Target user: {user.username} (role: {user.role}, status: {user.status})")
        
        if user.role == 'root' and current_user.role != 'root':
            logger.warning(f"Non-root user {current_user.username} attempted to change root user status")
            return None, "Only root users can change root user status"
        
        # Toggle status
        new_status = 'inactive' if user.status == 'active' else 'active'
        user.status = new_status
        db.session.commit()
        logger.info(f"Status changed to {new_status} for user {user.username}")
        
        # Create audit log entry
        user_agent = request.headers.get('User-Agent', '')
        ip = request.remote_addr
        
        AuditLog.log(
            user_id=current_user_id,
            action='toggle_user_status',
            details=f"Changed {user.username}'s status to {new_status} (ID: {user_id})",
            ip_address=ip,
            user_agent=user_agent
        )
        logger.info(f"Audit log created for user status change")
        
        return user, None
    except Exception as e:
        logger.error(f"Error toggling user status: {str(e)}", exc_info=True)
        db.session.rollback()
        return None, f"Server error: {str(e)}"

def bulk_import_users(file_data, current_user_id, auto_generate_username=False, username_not_required=False, role=None):
    """
    Import multiple users from Excel file - optimized for large batches (up to 1000+ users)
    Expected columns: fullName, email, role, and other optional fields
    
    For brosis users: studentId is required, username is optional (auto-generated if missing)
    For other roles: username is required
    
    Parameters:
    - file_data: Binary content of the Excel file
    - current_user_id: ID of the user performing the import
    - auto_generate_username: Whether to auto-generate usernames for users with role=brosis
    - username_not_required: Whether username is not required for students (brosis role)
    - role: Role to assign to all imported users (if specified)
    
    Returns: dict with success count, error count, and details of errors
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Parse Excel file - optimized using engine='openpyxl'
        df = pd.read_excel(io.BytesIO(file_data), engine='openpyxl')
        
        # Check required columns
        required_columns = ['email', 'fullName']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                "success": 0,
                "error": len(df),
                "message": f"Missing required columns: {', '.join(missing_columns)}",
                "details": []
            }
        
        # Initialize counters
        success_count = 0
        error_count = 0
        error_details = []
        
        # Get all areas and houses from the database for validation (one-time query)
        from app.models.models import Area, House
        
        # Cache area and house data for fast lookups
        # Create case-insensitive dictionaries for areas and houses
        areas_query = Area.query.all()
        areas_dict = {}  # Maps lowercase area name to area ID
        areas_orig = {}  # Maps lowercase area name to original capitalization
        area_id_to_lower_name = {}  # Maps area ID to lowercase name for house mapping
        
        for area in areas_query:
            lower_name = area.name.lower()
            areas_dict[lower_name] = area.id
            areas_orig[lower_name] = area.name
            area_id_to_lower_name[area.id] = lower_name
        
        houses_dict = {}  # Maps lowercase area name to list of lowercase house names
        houses_orig = {}  # Maps lowercase area name to dict mapping lowercase house name to original capitalization
        
        # Optimize the house lookup - do one query instead of N queries
        all_houses = House.query.all()
        for house in all_houses:
            # Directly map from area_id to lowercase area name
            area_name_lower = area_id_to_lower_name.get(house.area_id)
            
            if area_name_lower:
                if area_name_lower not in houses_dict:
                    houses_dict[area_name_lower] = []
                    houses_orig[area_name_lower] = {}
                
                house_name_lower = house.name.lower()
                houses_dict[area_name_lower].append(house_name_lower)
                houses_orig[area_name_lower][house_name_lower] = house.name
        
        # Cache existing usernames and emails for fast duplicate checking (one-time query)
        existing_usernames = {user.username.lower(): user.username for user in User.query.all()}
        existing_emails = {user.email.lower(): user.email for user in User.query.all()}
        
        # Process users in batches to optimize memory usage and database performance
        BATCH_SIZE = 100  # Process 100 users at a time
        
        # First validate all data to catch errors before any database changes
        valid_users = []
        
        # Extract and validate all users first (only validation, no DB operations yet)
        for index, row in df.iterrows():
            try:
                # Extract user data from row
                user_data = {
                    'username': str(row.get('username', '')).strip(),
                    'email': str(row.get('email', '')).strip(),
                    'fullName': str(row.get('fullName', '')).strip(),
                    'phone': str(row.get('phone', '')) if 'phone' in row and not pd.isna(row['phone']) else None,
                    'area': str(row.get('area', '')) if 'area' in row and not pd.isna(row['area']) else None,
                    'house': str(row.get('house', '')) if 'house' in row and not pd.isna(row['house']) else None,
                    'role': str(row.get('role', 'brosis')).lower() if 'role' in row and not pd.isna(row['role']) else 'brosis',
                    'status': str(row.get('status', 'active')).lower() if 'status' in row and not pd.isna(row['status']) else 'active',
                    'student_id': str(row.get('studentId', '')) if 'studentId' in row and not pd.isna(row['studentId']) else None,
                    'row_number': index + 2  # +2 because Excel rows are 1-indexed and header is row 1
                }
                
                # Auto-generate username for brosis users if not provided but have fullName and student_id
                if (not user_data['username'] or user_data['username'] == '') and \
                   user_data['role'] == 'brosis' and \
                   user_data['fullName'] and \
                   user_data['student_id']:
                    user_data['username'] = generate_username_from_fullname_and_student_id(
                        user_data['fullName'], 
                        user_data['student_id']
                    )
                    logger.info(f"Auto-generated username '{user_data['username']}' for BroSis user at row {user_data['row_number']}")
                
                # Basic validation
                # Validate role
                if user_data['role'] not in ['admin', 'mentor', 'brosis']:
                    user_data['role'] = 'brosis'
                
                # Validate status
                if user_data['status'] not in ['active', 'inactive']:
                    user_data['status'] = 'active'
                
                # Check required fields
                missing_fields = []
                
                # Email và fullName luôn bắt buộc
                if not user_data['email']:
                    missing_fields.append('email')
                
                if not user_data['fullName']:
                    missing_fields.append('fullName')
                
                # Username handling with special cases for brosis role
                if not user_data['username']:
                    # If username_not_required flag is set and role is brosis, we'll auto-generate it later
                    if username_not_required and (user_data['role'] == 'brosis' or role == 'brosis'):
                        # Generate username from student_id if available, otherwise from email
                        if user_data['student_id']:
                            user_data['username'] = f"student-{user_data['student_id']}"
                        elif user_data['email']:
                            # Create username from email (remove domain and special chars)
                            email_username = user_data['email'].split('@')[0].replace('.', '-')
                            user_data['username'] = f"student-{email_username}"
                        else:
                            # Last resort - generate random username
                            user_data['username'] = f"student-{int(time.time())}-{random.randint(1000, 9999)}"
                        
                        logger.info(f"Auto-generated username '{user_data['username']}' for BroSis user at row {user_data['row_number']}")
                    elif user_data['role'] != 'brosis' and role != 'brosis':
                        # Username is still required for non-brosis roles
                        missing_fields.append('username')
                
                if missing_fields:
                    raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
                # Check username and email duplicates (fast in-memory check)
                if user_data['username'].lower() in existing_usernames:
                    raise ValueError(f"Username '{user_data['username']}' already exists")
                
                if user_data['email'].lower() in existing_emails:
                    raise ValueError(f"Email '{user_data['email']}' already exists")
                
                # Add to "taken" list to prevent duplicates within the import file itself
                existing_usernames[user_data['username'].lower()] = user_data['username']
                existing_emails[user_data['email'].lower()] = user_data['email']
                
                # Check if 'brosis' role requires student_id
                if user_data['role'] == 'brosis' and (not user_data['student_id'] or user_data['student_id'].strip() == ''):
                    raise ValueError("Student ID is required for BroSis users")
                
                # Validate area and house if provided
                if user_data['area']:
                    area_lower = user_data['area'].lower()
                    if area_lower not in areas_dict:
                        valid_areas = ", ".join(areas_orig.values())  # Use original capitalization for display
                        raise ValueError(f"Invalid Area: '{user_data['area']}'. Please use one of the valid areas: {valid_areas}")
                    
                    # Use original capitalization for area in final data
                    user_data['area'] = areas_orig[area_lower]
                    
                    # If house is provided, validate it belongs to the area
                    if user_data['house']:
                        house_lower = user_data['house'].lower()
                        if area_lower not in houses_dict:
                            raise ValueError(f"Area '{user_data['area']}' exists but has no houses assigned to it.")
                        elif house_lower not in houses_dict[area_lower]:
                            valid_houses = ", ".join([houses_orig[area_lower][h] for h in houses_dict[area_lower]])
                            raise ValueError(f"Invalid House: '{user_data['house']}' does not exist in Area '{user_data['area']}'. Valid houses for this area are: {valid_houses}")
                        else:
                            # Use original capitalization for house in final data
                            user_data['house'] = houses_orig[area_lower][house_lower]
                
                # If validation passes, add to valid users
                valid_users.append(user_data)
                
            except Exception as e:
                error_count += 1
                error_details.append({
                    "row": index + 2,
                    "username": str(row.get('username', 'Unknown')),
                    "email": str(row.get('email', 'Unknown')),
                    "error": str(e)
                })
                logger.warning(f"Error validating user at row {index + 2}: {str(e)}")
        
        # Process the valid users in batches
        total_users = len(valid_users)
        total_batches = (total_users + BATCH_SIZE - 1) // BATCH_SIZE  # Ceiling division
        
        logger.info(f"Found {total_users} valid users to import in {total_batches} batches")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, total_users)
            batch_users = valid_users[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_num + 1}/{total_batches}, users {start_idx + 1}-{end_idx}")
            
            # Create a list of new user objects to bulk insert
            new_users = []
            
            for user_data in batch_users:
                try:
                    # For admin users, set default house to "FPT + Area" if area is provided but house is not
                    if user_data['role'] == 'admin' and user_data['area'] and not user_data['house']:
                        user_data['house'] = f"FPT {user_data['area']}"
                    
                    # Prepare user object
                    is_admin = (user_data['role'] == 'admin')
                    is_root = False  # We don't allow creating root users through import
                    
                    new_user = User(
                        username=user_data['username'], 
                        email=user_data['email'],
                        fullName=user_data['fullName'],
                        phone=user_data['phone'],
                        area=user_data['area'],
                        house=user_data['house'],
                        is_admin=is_admin,  # Keep for backward compatibility
                        is_root=is_root,    # Keep for backward compatibility
                        role=user_data['role'],
                        status=user_data['status'],
                        student_id=user_data['student_id'] if user_data['role'] == 'brosis' else None,
                        password_change_required=True
                    )
                    
                    # Set password (same as username)
                    new_user.set_password(user_data['username'], hash_type="sha256")
                    
                    # Add to batch
                    new_users.append(new_user)
                    
                except Exception as e:
                    error_count += 1
                    error_details.append({
                        "row": user_data['row_number'],
                        "username": user_data['username'],
                        "email": user_data['email'],
                        "error": f"Error creating user: {str(e)}"
                    })
                    logger.error(f"Error creating user {user_data['username']}: {str(e)}")
            
            # Bulk insert the batch of users
            if new_users:
                try:
                    # Use bulk_save_objects for optimal performance
                    db.session.bulk_save_objects(new_users)
                    db.session.commit()
                    success_count += len(new_users)
                    
                    # Create a single audit log entry for the batch
                    user_agent = request.headers.get('User-Agent', '')
                    ip = request.remote_addr
                    AuditLog.log(
                        user_id=current_user_id,
                        action='batch_create_users',
                        details=f"Batch imported {len(new_users)} users (batch {batch_num + 1}/{total_batches})",
                        ip_address=ip,
                        user_agent=user_agent
                    )
                    
                except Exception as e:
                    # If batch fails, rollback and add errors for all users in the batch
                    db.session.rollback()
                    logger.error(f"Batch insert failed: {str(e)}")
                    
                    # Mark all users in this batch as failed
                    for user_data in batch_users:
                        error_count += 1
                        error_details.append({
                            "row": user_data['row_number'],
                            "username": user_data['username'],
                            "email": user_data['email'],
                            "error": f"Database error: {str(e)}"
                        })
        
        return {
            "success": success_count,
            "error": error_count,
            "message": f"Imported {success_count} users successfully, {error_count} failed",
            "details": error_details
        }
        
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": 0,
            "error": 1,
            "message": f"Failed to process Excel file: {str(e)}",
            "details": []
        }

def generate_username_from_fullname_and_student_id(fullName, student_id):

    if not fullName or not student_id:
        return ""
    
    # Extract name parts (assuming Vietnamese name format)
    name_parts = fullName.lower().strip().split(' ')
    
    # In Vietnamese names:
    # - First name is the LAST part of the full name
    # - Last name is the FIRST part of the full name
    # - Middle names are everything in between
    
    # Get the first name (last word in Vietnamese names)
    first_name = name_parts[-1] if name_parts else ""
    
    # Get the first letter of last name and each middle name (everything except first name)
    initials = ''.join([part[0] for part in name_parts[:-1]]) if len(name_parts) > 1 else ""
    
    return first_name + initials + student_id.lower()
