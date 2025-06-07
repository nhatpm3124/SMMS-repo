from flask import jsonify, request
from flask_jwt_extended import jwt_required
from app.models.models import AuditLog, db, User, Area, House
from app.models.student import Student
from sqlalchemy import or_, and_
import logging
from app.services.auth import get_current_user
import random
from collections import defaultdict
from sqlalchemy import func
from flask import current_app

logger = logging.getLogger(__name__)

def get_all_students(page=1, per_page=20, filters=None, sort_by='id', sort_desc=False):
    """
    Get all students with pagination, filtering and sorting.
    Optimized for large datasets and responsive UI.
    
    Args:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, range: 10-100)
        filters (dict): Filter conditions
        sort_by (str): Column to sort by (default: 'id')
        sort_desc (bool): Sort in descending order (default: False)
        
    Returns:
        dict: Paginated student data with metadata
    """
    try:
        # Start with optimized base query
        query = Student.query.order_by(Student.id.desc())
        
        # Apply filters efficiently using joins when needed
        if filters:
            # Search filter - use database indexing for performance
            if 'search' in filters and filters['search']:
                search_term = f"%{filters['search'].strip()}%"
                # Use OR conditions efficiently with indexes
                # The ILIKE operator supports Unicode characters including Vietnamese with diacritics
                query = query.outerjoin(User, Student.user_id == User.id).filter(
                    or_(
                        Student.full_name.ilike(search_term),
                        Student.email.ilike(search_term),
                        Student.student_id.ilike(search_term),
                        User.full_name.ilike(search_term)
                    )
                )
            
            # Status filter - direct equality check is fast
            if 'status' in filters and filters['status']:
                query = query.filter(Student.status == filters['status'])
                
            # Area filter - use join if area relationships exist
            if 'area' in filters and filters['area']:
                query = query.filter(Student.area == filters['area'])
                
            # House filter - use join if house relationships exist
            if 'house' in filters and filters['house']:
                query = query.filter(Student.house == filters['house'])
                
            # Has House filter - check whether house field is set or not
            if 'has_house' in filters:
                has_house = filters['has_house']
                if has_house is True:
                    # Find students with non-empty house field
                    query = query.filter(Student.house.isnot(None), Student.house != '')
                else:
                    # Find students with empty or null house field
                    query = query.filter(or_(Student.house.is_(None), Student.house == ''))
                
            # Matched filter - use optimized boolean check
            if 'matched' in filters:
                matched_value = filters['matched'].lower() == 'true'
                logger.info(f"Processing matched filter: {filters['matched']} => boolean: {matched_value}")
                query = query.filter(Student.matched == matched_value)
                
            # User ID filter - for limiting students to specific brosis user
            if 'user_id' in filters and filters['user_id']:
                user_id = filters['user_id']
                logger.info(f"Filtering students by user_id: {user_id}")
                query = query.filter(Student.user_id == user_id)
            
            # Brosis filter - find students assigned to brosis with the given name
            if 'brosisFilter' in filters and filters['brosisFilter']:
                brosis_term = f"%{filters['brosisFilter'].strip()}%"
                # ILIKE supports Unicode characters including Vietnamese with diacritics
                logger.info(f"Applying brosis filter with term: '{filters['brosisFilter']}', search pattern: '{brosis_term}'")
                # Use outerjoin instead of join to ensure we don't lose students in the query
                if not any(isinstance(j, tuple) and j[0] is User for j in query._join_entities):
                    query = query.outerjoin(User, Student.user_id == User.id)
                query = query.filter(User.full_name.ilike(brosis_term))
                logger.info(f"Applied brosis filter, SQL: {str(query)}")
            
            logger.info(f"Applied student filters: {filters}")
        
        # Always use pagination for large datasets
        try:
            # Get total count efficiently
            total = query.count()
            
            # Calculate pagination metadata
            total_pages = (total + per_page - 1) // per_page
            has_next = page < total_pages
            has_prev = page > 1
            
            # Get paginated results with limit/offset
            students = query.limit(per_page).offset((page - 1) * per_page).all()
            
            return {
                "students": students,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "filters_active": bool(filters)  # Indicate if any filters are active
            }
        
        except Exception as e:
            logger.error(f"Error in pagination: {str(e)}")
            # Return empty result set with pagination metadata
            return {
                "students": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False,
                "error": str(e)
            }
            
    except Exception as e:
        logger.error(f"Error getting students: {str(e)}")
        return []


def create_student(student_data):
    """
    Create a new student
    
    Args:
        student_data (dict): Student data
        
    Returns:
        tuple: (Student object, error message)
    """
    try:
        # Check if required fields are present
        required_fields = ['studentId', 'fullName', 'email', 'phone', 'parentPhone', 'address']
        missing_fields = [field for field in required_fields if field not in student_data]
        
        if missing_fields:
            return None, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Check if student ID already exists
        existing_student = Student.query.filter(Student.student_id == student_data['studentId']).first()
        if existing_student:
            return None, f"Student with ID '{student_data['studentId']}' already exists"
        
        # Create new student
        new_student = Student(
            student_id=student_data['studentId'],
            full_name=student_data['fullName'],
            email=student_data['email'],
            phone=student_data['phone'],  # Required field
            parent_phone=student_data['parentPhone'],  # Required field
            address=student_data['address'],  # Required field
            area=student_data.get('area'),
            house=student_data.get('house'),
            area_id=student_data.get('areaId'),
            house_id=student_data.get('houseId'),
            status=student_data.get('status', 'pending'),  # Default to pending
            notes=student_data.get('notes')
        )
        
        db.session.add(new_student)
        db.session.commit()
        
        return new_student, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating student: {str(e)}")
        return None, f"Error creating student: {str(e)}"


def update_student(student_id, student_data):
    """
    Update an existing student
    
    Args:
        student_id (int): ID of student to update
        student_data (dict): Updated student data
        
    Returns:
        tuple: (Student object, error message)
    """
    try:
        # Get student
        student = Student.query.get(student_id)
        if not student:
            return None, f"Student with ID {student_id} not found"
        
        # Update fields
        if 'studentId' in student_data:
            # Check if new student ID already exists
            if student_data['studentId'] != student.student_id:
                existing = Student.query.filter(Student.student_id == student_data['studentId']).first()
                if existing:
                    return None, f"Student with ID '{student_data['studentId']}' already exists"
            student.student_id = student_data['studentId']
            
        if 'fullName' in student_data:
            student.full_name = student_data['fullName']
            
        if 'email' in student_data:
            student.email = student_data['email']
            
        if 'phone' in student_data:
            student.phone = student_data['phone']
            
        if 'parentPhone' in student_data:
            student.parent_phone = student_data['parentPhone']
        
        if 'parent_phone' in student_data:
            student.parent_phone = student_data['parent_phone']
            
        if 'area' in student_data:
            student.area = student_data['area']
            
        if 'house' in student_data:
            student.house = student_data['house']
            
        if 'areaId' in student_data:
            student.area_id = student_data['areaId']
            
        if 'houseId' in student_data:
            student.house_id = student_data['houseId']
            
        if 'status' in student_data:
            student.status = student_data['status']
            
        if 'matched' in student_data:
            student.matched = student_data['matched']
            
        if 'userId' in student_data:
            student.user_id = student_data['userId']
            if student_data['userId']:
                student.matched = True
            else:
                student.matched = False
                
        if 'notes' in student_data:
            student.notes = student_data['notes']
            
        db.session.commit()
        
        return student, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating student: {str(e)}")
        return None, f"Error updating student: {str(e)}"


def delete_student(student_id):
    """
    Delete a student
    
    Args:
        student_id (int): ID of student to delete
        
    Returns:
        tuple: (Success message, error message)
    """
    try:
        student = Student.query.get(student_id)
        if not student:
            return None, f"Student with ID {student_id} not found"
            
        db.session.delete(student)
        db.session.commit()
        
        return {"message": "Student deleted successfully"}, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting student: {str(e)}")
        return None, f"Error deleting student: {str(e)}"


def toggle_student_status(student_id):
    """
    Toggle a student's status between active and inactive
    
    Args:
        student_id (int): ID of student to toggle status
        
    Returns:
        tuple: (Student object, error message)
    """
    try:
        student = Student.query.get(student_id)
        if not student:
            return None, f"Student with ID {student_id} not found"
            
        student.status = 'inactive' if student.status == 'active' else 'active'
        db.session.commit()
        
        return student, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling student status: {str(e)}")
        return None, f"Error toggling student status: {str(e)}"


def map_student_to_user(student_id, user_id):
    """
    Map a student to a mentor/brosis user
    
    Args:
        student_id (int): ID of student
        user_id (int): ID of user (mentor/brosis)
        
    Returns:
        tuple: (Student object, error message)
    """
    try:
        student = Student.query.get(student_id)
        if not student:
            return None, f"Student with ID {student_id} not found"
            
        user = User.query.get(user_id)
        if not user:
            return None, f"User with ID {user_id} not found"
            
        # Update student
        student.user_id = user_id
        student.matched = True
        
        # Copy mentor's house and area to student
        if user.house:
            student.house = user.house
            
            # Look up the house in the database to get its ID
            house = House.query.filter_by(name=user.house).first()
            if house:
                student.house_id = house.id
        
        if user.area:
            student.area = user.area
            
            # Look up the area in the database to get its ID
            area = Area.query.filter_by(name=user.area).first()
            if area:
                student.area_id = area.id
        
        db.session.commit()
        
        return student, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error mapping student to user: {str(e)}")
        return None, f"Error mapping student to user: {str(e)}"


def unmap_student(student_id):
    """
    Unmaps a student from their mentor/brosis user while preserving 
    the student's house and area information.
    
    Args:
        student_id (int): The ID of the student to unmap
        
    Returns:
        tuple: (Student, error_message)
    """
    try:
        # Find the student
        student = Student.query.get(student_id)
        
        if not student:
            return None, f"Student with ID {student_id} not found"
        
        # If student is already unmatched, return early
        if not student.matched or not student.user_id:
            return student, "Student is already unmatched"
        
        # Store the previous mentor/user ID for logging
        previous_user_id = student.user_id
        
        # Unmap by setting user_id to None and matched to False
        # Important: We do NOT change area or house values
        student.user_id = None
        student.matched = False
        
        # Commit changes
        db.session.commit()
        
        logger.info(f"Unmapped student {student_id} (previously mapped to user {previous_user_id})")
        return student, None
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error unmapping student: {str(e)}")
        return None, f"Error unmapping student: {str(e)}"


def fisher_yates_shuffle(arr):
    """
    Implements the Fisher-Yates shuffle algorithm for randomizing an array in-place.
    This is a more efficient and unbiased shuffle algorithm than random.shuffle().
    """
    n = len(arr)
    for i in range(n - 1, 0, -1):
        j = random.randint(0, i)
        arr[i], arr[j] = arr[j], arr[i]
    return arr


def distribute_students_to_houses(students, area):
    """
    Distributes a list of students evenly among houses within a given area.
    Uses the Fisher-Yates algorithm to randomize before distribution.
    
    Args:
        students: List of Student objects to distribute
        area: Area name to find houses for
        
    Returns:
        Dictionary mapping each student to their assigned house
    """
    if not students or not area:
        return {}
        
    # Get all houses for this area
    from app.models.models import House, Area
    
    area_obj = Area.query.filter_by(name=area).first()
    if not area_obj:
        current_app.logger.warning(f"No area found with name: {area}")
        return {}
        
    houses = House.query.filter_by(area_id=area_obj.id).all()
    if not houses:
        current_app.logger.warning(f"No houses found for area: {area}")
        return {}
    
    # Get current student counts for each house to ensure even distribution
    from app.models.student import Student
    
    house_counts = {}
    for house in houses:
        count = Student.query.filter_by(house=house.name, area=area).count()
        house_counts[house.name] = count
    
    # Sort houses by their current student count (ascending)
    sorted_houses = sorted(houses, key=lambda h: house_counts.get(h.name, 0))
    
    # Shuffle students using Fisher-Yates algorithm
    shuffled_students = fisher_yates_shuffle(students.copy())
    
    # Assign house to each student
    student_house_mapping = {}
    
    # If we have no students or houses, return empty mapping
    if not shuffled_students or not sorted_houses:
        return student_house_mapping
    
    # Calculate how many students should be in each house for even distribution
    total_students = sum(house_counts.values()) + len(shuffled_students)
    num_houses = len(sorted_houses)
    target_per_house = total_students // num_houses
    remainder = total_students % num_houses
    
    # Calculate target counts for each house
    target_counts = {}
    for i, house in enumerate(sorted_houses):
        # Distribute remainder among first 'remainder' houses
        extra = 1 if i < remainder else 0
        target_counts[house.name] = target_per_house + extra
    
    # Calculate how many more students each house needs
    needed_counts = {}
    for house in sorted_houses:
        current_count = house_counts.get(house.name, 0)
        target = target_counts[house.name]
        needed_counts[house.name] = max(0, target - current_count)
    
    # Sort houses by how many more students they need (descending)
    distribution_order = sorted(
        sorted_houses, 
        key=lambda h: needed_counts.get(h.name, 0), 
        reverse=True
    )
    
    # Distribute students to houses
    house_index = 0
    for student in shuffled_students:
        # Find next house that needs students
        while house_index < len(distribution_order):
            house = distribution_order[house_index]
            if needed_counts[house.name] > 0:
                student_house_mapping[student] = house.name
                needed_counts[house.name] -= 1
                break
            house_index += 1
            
        # If all houses have reached their target, start over
        if house_index >= len(distribution_order):
            house_index = 0
            # Recalculate needed counts (should be all zeros now, but adding one to each)
            for house in distribution_order:
                needed_counts[house.name] += 1
            # Distribute to first house in order
            house = distribution_order[house_index]
            student_house_mapping[student] = house.name
            needed_counts[house.name] -= 1
            house_index += 1
    
    return student_house_mapping


def import_students_from_file(file_data, admin_area=None):

    try:
        imported_students = []
        errors = []
        batch_size = 100  # Process records in batches of 100
        
        # Pre-validate all records first - this helps catch errors early
        valid_records = []
        student_ids = set()  # For fast duplicate checking
        
        # First, get all existing student IDs in one query for efficient duplicate checking
        existing_student_ids = {s[0] for s in db.session.query(Student.student_id).all()}
        
        # Pre-validate all records
        for idx, row in enumerate(file_data, start=2):  # Start from 2 to account for header row in Excel
            try:
                # Check required fields
                required_fields = ['studentId', 'fullName', 'email', 'phone', 'parentPhone', 'address']
                missing_fields = [field for field in required_fields if field not in row or not row[field]]
                
                if missing_fields:
                    errors.append({
                        "row": idx,
                        "error": f"Missing required fields: {', '.join(missing_fields)}"
                    })
                    continue
                
                # Check for duplicate student ID in the existing database
                if row['studentId'] in existing_student_ids:
                    errors.append({
                        "row": idx,
                        "error": f"Student with ID '{row['studentId']}' already exists"
                    })
                    continue
                
                # Check for duplicates within the imported data
                if row['studentId'] in student_ids:
                    errors.append({
                        "row": idx,
                        "error": f"Duplicate student ID '{row['studentId']}' in import data"
                    })
                    continue
                
                student_ids.add(row['studentId'])
                valid_records.append((idx, row))
            
            except Exception as e:
                errors.append({
                    "row": idx,
                    "error": f"Error validating row: {str(e)}"
                })
        
        # Group valid records by area for even distribution
        area_students = defaultdict(list)
        area_records = defaultdict(list)
        
        # Process valid records in batches
        for i in range(0, len(valid_records), batch_size):
            batch = valid_records[i:i+batch_size]
            batch_students = []
            
            for idx, row in batch:
                try:
                    # Process area field
                    area = admin_area if admin_area else row.get('area')
                    
                    # Create new Student object directly
                    new_student = Student(
                        student_id=row['studentId'],
                        full_name=row['fullName'],
                        email=row['email'],
                        phone=row['phone'],
                        parent_phone=row['parentPhone'],
                        address=row['address'],
                        area=area,
                        # House will be assigned later after all students are processed
                        status='pending'  # Always set status to pending for imported students
                    )
                    
                    # Don't add to session yet, collect by area first
                    if area:
                        area_students[area].append(new_student)
                        area_records[area].append((idx, row))
                    else:
                        # If no area, can't distribute to houses, so add directly
                        db.session.add(new_student)
                        batch_students.append(new_student)
                    
                except Exception as e:
                    errors.append({
                        "row": idx,
                        "error": f"Error processing row: {str(e)}"
                    })
            
            # Process students with no area
            try:
                # Add students without area to database
                if batch_students:
                    db.session.flush()
                    imported_students.extend(batch_students)
            except Exception as e:
                db.session.rollback()
                # Handle error for students without area
                current_app.logger.error(f"Error adding students without area: {str(e)}")
                for student in batch_students:
                    try:
                        # Try adding one by one
                        db.session.add(student)
                        db.session.flush()
                        imported_students.append(student)
                    except Exception as inner_e:
                        errors.append({
                            "row": "Unknown",
                            "error": f"Error adding student: {str(inner_e)}"
                        })
        
        # Now distribute students by area to houses
        for area, students in area_students.items():
            # Get house assignments for students
            student_house_mapping = distribute_students_to_houses(students, area)
            
            # Apply house assignments and add to session
            for student in students:
                if student in student_house_mapping:
                    student.house = student_house_mapping[student]
                
                try:
                    db.session.add(student)
                    db.session.flush()  # Check for database errors
                    imported_students.append(student)
                except Exception as e:
                    db.session.rollback()
                    # Find the corresponding record
                    idx = next((rec[0] for rec in area_records[area] if rec[1]['studentId'] == student.student_id), "Unknown")
                    errors.append({
                        "row": idx,
                        "error": f"Error adding student to database: {str(e)}"
                    })
        
        # Commit all changes if there are successful imports
        if imported_students:
            db.session.commit()
        
        # Generate summary stats
        summary = {
            "total_rows": len(file_data),
            "successful_imports": len(imported_students),
            "failed_imports": len(errors),
            "area_inherited": admin_area is not None,
            "auto_house_distribution": True  # Indicate house distribution was applied
        }
        
        return imported_students, errors, summary
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error importing students: {str(e)}")
        return [], [{"row": "N/A", "error": f"Error importing file: {str(e)}"}], {
            "total_rows": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "error": str(e)
        }


def get_all_student_ids(filters=None):
    """
    Get all student IDs matching the given filters without pagination.
    Used for "select all across pages" functionality.
    
    Args:
        filters (dict): Filter conditions (same as get_all_students)
        
    Returns:
        list: List of student IDs matching the filters
    """
    try:
        # Start with base query that only selects the ID column for efficiency
        query = Student.query.with_entities(Student.id)
        
        # Apply the same filters as in get_all_students
        if filters:
            # Search filter
            if 'search' in filters and filters['search']:
                search_term = f"%{filters['search'].strip()}%"
                query = query.filter(
                    or_(
                        Student.full_name.ilike(search_term),
                        Student.email.ilike(search_term),
                        Student.student_id.ilike(search_term)
                    )
                )
            
            # Status filter
            if 'status' in filters and filters['status']:
                query = query.filter(Student.status == filters['status'])
                
            # Area filter
            if 'area' in filters and filters['area']:
                query = query.filter(Student.area == filters['area'])
                
            # House filter
            if 'house' in filters and filters['house']:
                query = query.filter(Student.house == filters['house'])
                
            # Matched filter
            if 'matched' in filters and filters['matched']:
                matched_value = filters['matched'].lower() == 'true'
                query = query.filter(Student.matched == matched_value)
            
            # Brosis filter - find students assigned to brosis with the given name
            if 'brosisFilter' in filters and filters['brosisFilter']:
                brosis_term = f"%{filters['brosisFilter'].strip()}%"
                # ILIKE supports Unicode characters including Vietnamese with diacritics
                logger.info(f"Applying brosis filter to student IDs with term: '{filters['brosisFilter']}'")
                # Use outerjoin instead of join to ensure we don't lose students in the query
                query = query.outerjoin(User, Student.user_id == User.id)
                query = query.filter(User.full_name.ilike(brosis_term))
            
            logger.info(f"Applied student ID filters: {filters}")
        
        # Execute query and extract IDs
        student_ids = [id for id, in query.all()]
        
        # Log the number of IDs found for monitoring
        logger.info(f"Found {len(student_ids)} student IDs matching filters")
        
        return student_ids
            
    except Exception as e:
        logger.error(f"Error getting student IDs: {str(e)}")
        return []
