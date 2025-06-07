from app.models.models import db, Group, GroupMember, User
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_
from datetime import datetime
import logging

def get_groups_for_mentor(mentor_id, area, house, page=1, per_page=10, filters=None):
    """
    Get all groups for a specific mentor with pagination and filtering
    
    Args:
        mentor_id (int): The mentor's user ID
        area (str): The mentor's area
        house (str): The mentor's house
        page (int): Page number for pagination
        per_page (int): Items per page
        filters (dict): Any additional filters to apply
        
    Returns:
        dict: A dictionary containing groups and pagination information
    """
    try:
        # Start with the base query for this mentor's groups
        query = Group.query.filter_by(mentor_id=mentor_id, area=area, house=house)
        
        # Apply additional filters
        if filters:
            if 'search' in filters and filters['search']:
                search_term = f"%{filters['search']}%"
                query = query.filter(Group.name.ilike(search_term))
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        # Apply pagination
        groups = query.order_by(Group.created_at.desc()).paginate(page=page, per_page=per_page)
        
        return {
            "groups": groups.items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev
        }
    
    except SQLAlchemyError as e:
        logging.error(f"Database error in get_groups_for_mentor: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in get_groups_for_mentor: {str(e)}")
        return None

def get_group_by_id(group_id, mentor_id=None):
    """
    Get a specific group by ID, optionally checking mentor ownership
    
    Args:
        group_id (int): The group ID
        mentor_id (int, optional): If provided, checks that the group belongs to this mentor
        
    Returns:
        Group: The group object if found, None otherwise
    """
    try:
        if mentor_id:
            return Group.query.filter_by(id=group_id, mentor_id=mentor_id).first()
        return Group.query.filter_by(id=group_id).first()
    except Exception as e:
        logging.error(f"Error in get_group_by_id: {str(e)}")
        return None

def create_group(mentor_id, name, description, area, house):
    """
    Create a new group
    
    Args:
        mentor_id (int): The mentor's user ID
        name (str): Group name
        description (str): Group description
        area (str): Area for the group
        house (str): House for the group
        
    Returns:
        Group: The created group object, or None on error
    """
    try:
        # Create new group
        new_group = Group(
            name=name,
            description=description,
            mentor_id=mentor_id,
            area=area,
            house=house
        )
        
        db.session.add(new_group)
        db.session.commit()
        
        return new_group
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error in create_group: {str(e)}")
        return None
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error in create_group: {str(e)}")
        return None

def update_group(group_id, mentor_id, data):
    """
    Update an existing group
    
    Args:
        group_id (int): The group ID to update
        mentor_id (int): The mentor's user ID (for ownership verification)
        data (dict): New data for the group
        
    Returns:
        Group: The updated group object, or None on error
    """
    try:
        group = get_group_by_id(group_id, mentor_id)
        
        if not group:
            return None
        
        # Update fields
        if 'name' in data:
            group.name = data['name']
        if 'description' in data:
            group.description = data['description']
        
        group.updated_at = datetime.utcnow()
        
        db.session.commit()
        return group
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error in update_group: {str(e)}")
        return None
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error in update_group: {str(e)}")
        return None

def delete_group(group_id, mentor_id):
    """
    Delete a group
    
    Args:
        group_id (int): The group ID to delete
        mentor_id (int): The mentor's user ID (for ownership verification)
        
    Returns:
        bool: True if successfully deleted, False otherwise
    """
    try:
        group = get_group_by_id(group_id, mentor_id)
        
        if not group:
            return False
        
        db.session.delete(group)
        db.session.commit()
        
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error in delete_group: {str(e)}")
        return False
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error in delete_group: {str(e)}")
        return False

def add_members_to_group(group_id, user_ids, mentor_id):
    """
    Add members to a group
    
    Args:
        group_id (int): The group ID
        user_ids (list): List of user IDs to add
        mentor_id (int): The mentor's user ID (for ownership verification)
        
    Returns:
        dict: A dictionary with success/failure counts and error messages
    """
    result = {"added": 0, "errors": 0, "messages": []}
    
    try:
        group = get_group_by_id(group_id, mentor_id)
        
        if not group:
            result["messages"].append("Group not found or you don't have permission")
            return result
        
        # Get existing member IDs
        existing_members = [member.user_id for member in group.members]
        
        for user_id in user_ids:
            if user_id in existing_members:
                result["messages"].append(f"User {user_id} is already in the group")
                result["errors"] += 1
                continue
                
            # Check that user exists and is a BroSis
            user = User.query.filter_by(id=user_id).first()
            if not user:
                result["messages"].append(f"User {user_id} not found")
                result["errors"] += 1
                continue
                
            if user.role != 'brosis':
                result["messages"].append(f"User {user_id} is not a BroSis user")
                result["errors"] += 1
                continue
                
            # Check that user is in the same area and house
            if user.area != group.area or user.house != group.house:
                result["messages"].append(f"User {user_id} is not in the same area/house")
                result["errors"] += 1
                continue
                
            # Add user to group
            new_member = GroupMember(group_id=group_id, user_id=user_id)
            db.session.add(new_member)
            result["added"] += 1
            
        db.session.commit()
        return result
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error in add_members_to_group: {str(e)}")
        result["messages"].append(f"Database error: {str(e)}")
        return result
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error in add_members_to_group: {str(e)}")
        result["messages"].append(f"Unexpected error: {str(e)}")
        return result

def remove_member_from_group(group_id, user_id, mentor_id):
    """
    Remove a member from a group
    
    Args:
        group_id (int): The group ID
        user_id (int): User ID to remove
        mentor_id (int): The mentor's user ID (for ownership verification)
        
    Returns:
        bool: True if successfully removed, False otherwise
    """
    try:
        group = get_group_by_id(group_id, mentor_id)
        
        if not group:
            return False
            
        member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        
        if not member:
            return False
            
        db.session.delete(member)
        
        # If this user was the group leader, remove them as leader
        if group.leader_id == user_id:
            group.leader_id = None
            
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error in remove_member_from_group: {str(e)}")
        return False
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error in remove_member_from_group: {str(e)}")
        return False

def assign_leader(group_id, user_id, mentor_id):
    """
    Assign a leader to a group
    
    Args:
        group_id (int): The group ID
        user_id (int): User ID to make leader
        mentor_id (int): The mentor's user ID (for ownership verification)
        
    Returns:
        Group: The updated group object, or None on error
    """
    try:
        group = get_group_by_id(group_id, mentor_id)
        
        if not group:
            return None
            
        # Check that the user is a member of the group
        member = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        if not member:
            return None
            
        # Assign as leader
        group.leader_id = user_id
        group.updated_at = datetime.utcnow()
        
        db.session.commit()
        return group
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error in assign_leader: {str(e)}")
        return None
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error in assign_leader: {str(e)}")
        return None

def remove_leader(group_id, mentor_id):
    """
    Remove the leader from a group
    
    Args:
        group_id (int): The group ID
        mentor_id (int): The mentor's user ID (for ownership verification)
        
    Returns:
        Group: The updated group object, or None on error
    """
    try:
        group = get_group_by_id(group_id, mentor_id)
        
        if not group:
            return None
            
        # Remove leader
        group.leader_id = None
        group.updated_at = datetime.utcnow()
        
        db.session.commit()
        return group
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error in remove_leader: {str(e)}")
        return None
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error in remove_leader: {str(e)}")
        return None 