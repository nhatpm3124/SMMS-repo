from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.services.auth import get_current_user
from app.models.models import AuditLog, User
from app.services.student_unmap import unmap_student
from app.models.student import Student
import logging

student_api = Blueprint('student_unmap_api', __name__)
logger = logging.getLogger(__name__)

@student_api.route('/students/<int:student_id>/unmap', methods=['POST'])
@jwt_required()
def unmap_student_endpoint(student_id):
    """Unmap a student from their mentor/brosis user (protected, admin only)"""
    try:
        # Check if user is authenticated and authorized
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
            
        if not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Get current student to check area access
        student = Student.query.get(student_id)
        if not student:
            return jsonify({"error": f"Student with ID {student_id} not found"}), 404
        
        # Check if student is actually mapped
        if not student.matched or not student.user_id:
            return jsonify({"error": "Student is not mapped to any mentor"}), 400
        
        # Record the previous mapping for audit log
        previous_user_id = student.user_id
        previous_user = User.query.get(previous_user_id)
        previous_username = previous_user.username if previous_user else "unknown"
        
        # Non-root users can only unmap students in their area
        if current_user.role != 'root' and student.area != current_user.area:
            return jsonify({"error": "You can only unmap students in your area"}), 403
        
        # Unmap student
        unmapped_student, error = unmap_student(student_id)
        
        if error:
            return jsonify({"error": error}), 400
        
        # Log unmapping
        AuditLog.log(
            user_id=current_user.id,
            action='unmap_student',
            details=f"Unmapped student {student.student_id} from user {previous_username}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        return jsonify(unmapped_student.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error unmapping student from user: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
