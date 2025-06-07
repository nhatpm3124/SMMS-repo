from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth import get_current_user
from app.services.group import (
    get_groups_for_mentor, get_group_by_id, create_group, update_group, delete_group,
    add_members_to_group, remove_member_from_group, assign_leader, remove_leader
)
from app.utils.cors import cors_preflight
import logging

group_api = Blueprint('group_api', __name__)

# Handle OPTIONS requests
@group_api.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@group_api.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    response = jsonify({"status": "ok"})
    return response

@group_api.route('/groups', methods=['GET'])
@jwt_required()
def get_groups():
    """Get all groups for the authenticated mentor"""
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
    
    # Only mentors, admins and root users can access groups
    if current_user.role not in ['mentor', 'admin', 'root']:
        return jsonify({"error": "Unauthorized. Only mentors can manage groups."}), 403
    
    # Get mentor's area and house
    mentor_area = current_user.area
    mentor_house = current_user.house
    
    if not mentor_area or not mentor_house:
        return jsonify({"error": "Mentor must have area and house assigned"}), 400
    
    # Default pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Additional filters
    filters = {}
    search = request.args.get('search')
    if search:
        filters['search'] = search
    
    # Get groups from service
    result = get_groups_for_mentor(
        mentor_id=current_user.id,
        area=mentor_area,
        house=mentor_house,
        page=page,
        per_page=per_page,
        filters=filters
    )
    
    if result is None:
        return jsonify({"error": "Error fetching groups"}), 500
    
    return jsonify({
        "groups": [group.to_dict() for group in result["groups"]],
        "pagination": {
            "total": result["total"],
            "page": result["page"],
            "per_page": result["per_page"],
            "total_pages": result["total_pages"],
            "has_next": result["has_next"],
            "has_prev": result["has_prev"]
        }
    })

@group_api.route('/groups/<int:group_id>', methods=['GET'])
@jwt_required()
def get_group(group_id):
    """Get a specific group by ID"""
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
    
    # Only mentors, admins and root users can access groups
    if current_user.role not in ['mentor', 'admin', 'root']:
        return jsonify({"error": "Unauthorized. Only mentors can manage groups."}), 403
    
    # Get group by ID, verifying ownership
    group = get_group_by_id(group_id, current_user.id)
    
    if not group:
        return jsonify({"error": "Group not found or you don't have permission"}), 404
    
    return jsonify(group.to_dict())

@group_api.route('/groups', methods=['POST'])
@jwt_required()
def create_new_group():
    """Create a new group"""
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
    
    # Only mentors, admins and root users can create groups
    if current_user.role not in ['mentor', 'admin', 'root']:
        return jsonify({"error": "Unauthorized. Only mentors can manage groups."}), 403
    
    # Get mentor's area and house
    mentor_area = current_user.area
    mentor_house = current_user.house
    
    if not mentor_area or not mentor_house:
        return jsonify({"error": "Mentor must have area and house assigned"}), 400
    
    # Validate required fields
    data = request.json
    if not data:
        return jsonify({"error": "Missing request data"}), 400
    
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({"error": "Group name is required"}), 400
    
    # Create group using service
    new_group = create_group(
        mentor_id=current_user.id,
        name=name,
        description=description,
        area=mentor_area,
        house=mentor_house
    )
    
    if not new_group:
        return jsonify({"error": "Error creating group"}), 500
    
    return jsonify({"message": "Group created successfully", "group": new_group.to_dict()}), 201

@group_api.route('/groups/<int:group_id>', methods=['PUT'])
@jwt_required()
def update_group_endpoint(group_id):
    """Update an existing group"""
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
    
    # Only mentors, admins and root users can update groups
    if current_user.role not in ['mentor', 'admin', 'root']:
        return jsonify({"error": "Unauthorized. Only mentors can manage groups."}), 403
    
    # Validate request data
    data = request.json
    if not data:
        return jsonify({"error": "Missing request data"}), 400
    
    if 'name' in data and not data['name']:
        return jsonify({"error": "Group name cannot be empty"}), 400
    
    # Update group using service
    updated_group = update_group(
        group_id=group_id,
        mentor_id=current_user.id,
        data=data
    )
    
    if not updated_group:
        return jsonify({"error": "Group not found or you don't have permission"}), 404
    
    return jsonify({"message": "Group updated successfully", "group": updated_group.to_dict()})

@group_api.route('/groups/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group_endpoint(group_id):
    """Delete a group"""
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
    
    # Only mentors, admins and root users can delete groups
    if current_user.role not in ['mentor', 'admin', 'root']:
        return jsonify({"error": "Unauthorized. Only mentors can manage groups."}), 403
    
    # Delete group using service
    success = delete_group(
        group_id=group_id,
        mentor_id=current_user.id
    )
    
    if not success:
        return jsonify({"error": "Group not found or you don't have permission"}), 404
    
    return jsonify({"message": "Group deleted successfully"})

@group_api.route('/groups/<int:group_id>/members', methods=['POST'])
@jwt_required()
def add_members(group_id):
    """Add members to a group"""
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
    
    # Only mentors, admins and root users can add members
    if current_user.role not in ['mentor', 'admin', 'root']:
        return jsonify({"error": "Unauthorized. Only mentors can manage groups."}), 403
    
    # Validate request data
    data = request.json
    if not data or 'user_ids' not in data:
        return jsonify({"error": "Missing user_ids in request data"}), 400
    
    user_ids = data['user_ids']
    if not isinstance(user_ids, list) or not user_ids:
        return jsonify({"error": "user_ids must be a non-empty list"}), 400
    
    # Add members using service
    result = add_members_to_group(
        group_id=group_id,
        user_ids=user_ids,
        mentor_id=current_user.id
    )
    
    if not result:
        return jsonify({"error": "Error adding members to group"}), 500
    
    # Check if there were any errors
    if result["errors"] > 0 and result["added"] == 0:
        return jsonify({
            "error": "Could not add any members to the group",
            "messages": result["messages"]
        }), 400
    
    return jsonify({
        "message": f"Added {result['added']} members to group",
        "warnings": result["messages"] if result["errors"] > 0 else []
    })

@group_api.route('/groups/<int:group_id>/members/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_member(group_id, user_id):
    """Remove a member from a group"""
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
    
    # Only mentors, admins and root users can remove members
    if current_user.role not in ['mentor', 'admin', 'root']:
        return jsonify({"error": "Unauthorized. Only mentors can manage groups."}), 403
    
    # Remove member using service
    success = remove_member_from_group(
        group_id=group_id,
        user_id=user_id,
        mentor_id=current_user.id
    )
    
    if not success:
        return jsonify({"error": "Member not found or you don't have permission"}), 404
    
    return jsonify({"message": "Member removed successfully"})

@group_api.route('/groups/<int:group_id>/leader/<int:user_id>', methods=['PUT'])
@jwt_required()
def assign_group_leader(group_id, user_id):
    """Assign a leader to a group"""
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
    
    # Only mentors, admins and root users can assign leaders
    if current_user.role not in ['mentor', 'admin', 'root']:
        return jsonify({"error": "Unauthorized. Only mentors can manage groups."}), 403
    
    # Assign leader using service
    updated_group = assign_leader(
        group_id=group_id,
        user_id=user_id,
        mentor_id=current_user.id
    )
    
    if not updated_group:
        return jsonify({"error": "Group not found, member not found, or you don't have permission"}), 404
    
    return jsonify({
        "message": "Leader assigned successfully",
        "group": updated_group.to_dict()
    })

@group_api.route('/groups/<int:group_id>/leader', methods=['DELETE'])
@jwt_required()
def remove_group_leader(group_id):
    """Remove the leader from a group"""
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
    
    # Only mentors, admins and root users can remove leaders
    if current_user.role not in ['mentor', 'admin', 'root']:
        return jsonify({"error": "Unauthorized. Only mentors can manage groups."}), 403
    
    # Remove leader using service
    updated_group = remove_leader(
        group_id=group_id,
        mentor_id=current_user.id
    )
    
    if not updated_group:
        return jsonify({"error": "Group not found or you don't have permission"}), 404
    
    return jsonify({
        "message": "Leader removed successfully",
        "group": updated_group.to_dict()
    }) 