# Simple students API that returns mock data
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth import get_current_user
from app.models.models import AuditLog
import logging

# Create a simple student routes blueprint
student_routes = Blueprint('student_routes', __name__)
logger = logging.getLogger(__name__)

@student_routes.route('/students', methods=['GET'])
@jwt_required()
def get_students():
    """Get all students (protected) with optional pagination and filtering"""
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
            logger.info(f"Area restriction applied for {current_user.username}: {current_user.area}")
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
        logger.info(f"Student filters applied: {filters}")
        
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
        
        return jsonify({
            "students": filtered_students,
            "pagination": {
                "total": len(filtered_students),
                "page": 1,
                "per_page": len(filtered_students),
                "total_pages": 1,
                "has_next": False,
                "has_prev": False
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching students: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
