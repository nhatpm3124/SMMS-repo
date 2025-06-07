from app.models.models import db
from app.models.student import Student
import logging

logger = logging.getLogger(__name__)

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
