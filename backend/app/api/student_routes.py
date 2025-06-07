import sys
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth import get_current_user
from app.models.models import AuditLog, User
from app.models.student import Student, db
import logging
import pandas as pd
import io
from datetime import datetime
import time

from app.services.student import create_student, delete_student, get_all_students, import_students_from_file, map_student_to_user, toggle_student_status, update_student, unmap_student

# Create blueprint with a different name
student_api = Blueprint('student_routes', __name__)
logger = logging.getLogger(__name__)

@student_api.route('/students', methods=['GET'])
@jwt_required()
def get_students():
    """Get all students (protected) with optional pagination and filtering"""
    try:
        # Check if user is authenticated
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Get pagination and sorting parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)  # Giảm mặc định xuống 20 để UI gọn hơn
        sort_by = request.args.get('sortBy', 'id')  # Mặc định sắp xếp theo id
        sort_desc = request.args.get('sortDesc', 'false').lower() == 'true'
            
        # Limit per_page to range 10-10000 for performance
        if per_page < 10:
            per_page = 10
        elif per_page > 10000:
            per_page = 10000
            
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
        
        # Has House filter - new filter to check if house field is set or not
        has_house = request.args.get('hasHouse')
        if has_house is not None:
            # Convert string to boolean: 'true' -> True, 'false' -> False
            has_house_bool = has_house.lower() == 'true'
            filters['has_house'] = has_house_bool
        
        # Brosis users can only see students assigned to them
        if current_user.role == 'brosis':
            # Brosis users can only see their assigned students
            filters['user_id'] = current_user.id
            filters['matched'] = 'true'
            logger.info(f"Brosis user restriction applied: only showing students assigned to {current_user.username}")
        # Area filter - apply area restriction for non-root users
        elif current_user.role != 'root':
            # Non-root, non-brosis users can only see students from their area
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
        
        # Get students with pagination, filtering and sorting
        result = get_all_students(
            page=page,
            per_page=per_page,
            filters=filters,
            sort_by=sort_by,
            sort_desc=sort_desc
        )
        
        if isinstance(result, dict):
            # Format response metadata with enhanced pagination info
            current_page = result["page"]
            total_pages = result["total_pages"]
            
            # Calculate page ranges for UI pagination
            show_pages = 5  # Số trang hiển thị trong UI
            page_range = []
            
            if total_pages <= show_pages:
                # Nếu tổng số trang ít hơn số trang cần hiển thị, hiện tất cả
                page_range = list(range(1, total_pages + 1))
            else:
                # Tính toán range trang để hiển thị
                if current_page <= 3:
                    # Đang ở gần trang đầu
                    page_range = list(range(1, 6))
                elif current_page >= total_pages - 2:
                    # Đang ở gần trang cuối
                    page_range = list(range(total_pages - 4, total_pages + 1))
                else:
                    # Đang ở giữa
                    page_range = list(range(current_page - 2, current_page + 3))
            
            pagination = {
                "total": result["total"],
                "page": current_page,
                "per_page": result["per_page"],
                "total_pages": total_pages,
                "has_next": result["has_next"],
                "has_prev": result["has_prev"],
                "sort_by": sort_by,
                "sort_desc": sort_desc,
                "showing_from": ((current_page - 1) * result["per_page"]) + 1,
                "showing_to": min(current_page * result["per_page"], result["total"]),
                "page_range": page_range,
                "first_page": 1,
                "last_page": total_pages,
                "display_first": current_page > 3,  # Có nên hiển thị nút về trang đầu
                "display_last": current_page < total_pages - 2,  # Có nên hiển thị nút về trang cuối
                "record_count": f"Hiển thị {((current_page - 1) * result['per_page']) + 1} đến {min(current_page * result['per_page'], result['total'])} trong tổng số {result['total']} bản ghi"
            }
            
            # Return paginated response with additional metadata
            return jsonify({
                "students": [student.to_dict() for student in result["students"]],
                "pagination": pagination,
                "filters_active": bool(filters)
            })
        # Error case - return empty response with default pagination
        return jsonify({
            "students": [],
            "pagination": {
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False,
                "showing_from": 0,
                "showing_to": 0,
                "page_range": []
            },
            "filters_active": bool(filters),
            "error": "Invalid response format from data service"
        })
        
    except Exception as e:
        logger.error(f"Error fetching students: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@student_api.route('/students', methods=['POST'])
@jwt_required()
def create_student_endpoint():
    """Create a new student (protected)"""
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
            logger.info(f"Setting student area to admin's area: {current_user.area}")
        
        # Create student
        student, error = create_student(data)
        
        if error:
            return jsonify({"error": error}), 400
        
        # Log creation
        AuditLog.log(
            user_id=current_user.id,
            action='create_student',
            details=f"Created student {data.get('studentId')}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        return jsonify(student.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating student: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@student_api.route('/students/<int:student_id>', methods=['PUT'])
@jwt_required()
def update_student_endpoint(student_id):
    """Update a student (protected)"""
    try:
        # Check if user is authenticated and authorized
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
            
        # Get student data from request
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get current student to check access
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({"error": f"Student with ID {student_id} not found"}), 404
        
        # Permission checks based on role
        if current_user.role == 'brosis':
            # Brosis can only update students assigned to them
            if student.user_id != current_user.id:
                return jsonify({"error": "You can only update students assigned to you"}), 403
                
            # Restrict the fields brosis can update
            allowed_fields = ['notes', 'status']
            invalid_fields = [field for field in data.keys() if field not in allowed_fields]
            
            # Normalize field names to be consistent (convert camelCase to snake_case)
            if 'parentPhone' in data and 'parent_phone' not in data:
                data['parent_phone'] = data['parentPhone']
                
            if invalid_fields:
                return jsonify({"error": f"Brosis users cannot update these fields: {', '.join(invalid_fields)}"}), 403
                
        elif current_user.role in ['admin', 'root']:
            # Admin and root have their own restrictions
            # Non-root users can only update students in their area
            if current_user.role != 'root' and student.area != current_user.area:
                return jsonify({"error": "You can only update students in your area"}), 403
        else:
            # Other roles don't have permission
            return jsonify({"error": "Permission denied"}), 403
            
        # Update student
        updated_student, error = update_student(student_id, data)
        
        if error:
            return jsonify({"error": error}), 400
        
        # Log update
        AuditLog.log(
            user_id=current_user.id,
            action='update_student',
            details=f"Updated student {student.student_id}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        return jsonify(updated_student.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error updating student: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
        
@student_api.route('/students/<int:student_id>', methods=['DELETE'])
@jwt_required()
def delete_student_endpoint(student_id):
    """Delete a student (protected, admin only)"""
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
        
        # Non-root users can only delete students in their area
        if current_user.role != 'root' and student.area != current_user.area:
            return jsonify({"error": "You can only delete students in your area"}), 403
            
        # Delete student
        result, error = delete_student(student_id)
        
        if error:
            return jsonify({"error": error}), 400
        
        # Log deletion
        AuditLog.log(
            user_id=current_user.id,
            action='delete_student',
            details=f"Deleted student {student.student_id}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
        
@student_api.route('/students/<int:student_id>/toggle-status', methods=['PUT'])
@jwt_required()
def toggle_student_status_endpoint(student_id):
    """Toggle a student's status between active and inactive (protected, admin only)"""
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
        
        # Non-root users can only update students in their area
        if current_user.role != 'root' and student.area != current_user.area:
            return jsonify({"error": "You can only update students in your area"}), 403
            
        # Toggle student status
        updated_student, error = toggle_student_status(student_id)
        
        if error:
            return jsonify({"error": error}), 400
        
        # Log status change
        AuditLog.log(
            user_id=current_user.id,
            action='toggle_student_status',
            details=f"Toggled status for student {student.student_id} to {updated_student.status}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        return jsonify(updated_student.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error toggling student status: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@student_api.route('/students/<int:student_id>/map', methods=['POST'])
@jwt_required()
def map_student_to_user_endpoint(student_id):
    """Map a student to a mentor/brosis user (protected, admin only)"""
    try:
        # Check if user is authenticated and authorized
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
            
        if not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Get mapping data from request
        data = request.json
        if not data or 'userId' not in data:
            return jsonify({"error": "User ID required"}), 400
            
        user_id = data['userId']
        
        # Get current student to check area access
        student = Student.query.get(student_id)
        if not student:
            return jsonify({"error": f"Student with ID {student_id} not found"}), 404
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": f"User with ID {user_id} not found"}), 404
        
        # Non-root users can only map students in their area
        if current_user.role != 'root' and student.area != current_user.area:
            return jsonify({"error": "You can only map students in your area"}), 403
            
        # Map student to user
        mapped_student, error = map_student_to_user(student_id, user_id)
        
        if error:
            return jsonify({"error": error}), 400
        
        # Log mapping
        AuditLog.log(
            user_id=current_user.id,
            action='map_student_to_user',
            details=f"Mapped student {student.student_id} to user {user.username}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        return jsonify(mapped_student.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error mapping student to user: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@student_api.route('/students/import', methods=['POST'])
@jwt_required()
def import_students_endpoint():
    """Import students from Excel or CSV file (protected, admin only)"""
    try:
        # Check if user is authenticated and authorized
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
            
        if not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Check if file is present in the request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "No file selected"}), 400
        
        # Check file extension
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            return jsonify({"error": "Unsupported file format. Please upload an Excel or CSV file."}), 400
        
        # Determine if preview mode or actual import
        preview_mode = request.form.get('preview', 'false').lower() == 'true'
        
        # Read file based on extension
        try:
            file_extension = file.filename.lower().split('.')[-1]
            
            if file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(file)
            else:  # csv
                df = pd.read_csv(file)
            
            # Check if file is empty
            if df.empty:
                return jsonify({"error": "The uploaded file is empty"}), 400
            
            # Check for required columns
            required_columns = ['studentId', 'fullName', 'email', 'phone', 'parentPhone', 'address']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return jsonify({
                    "error": f"The file is missing required columns: {', '.join(missing_columns)}. Please use the template provided."
                }), 400
            
            # Convert DataFrame to list of dictionaries
            data = df.replace({pd.NA: None}).to_dict('records')
            
            # Clean up data (strip whitespace, etc.)
            for record in data:
                for key, value in record.items():
                    if isinstance(value, str):
                        record[key] = value.strip()
            
            # If preview mode, just return the data
            if preview_mode:
                # Add area inherited from admin user if applicable
                if current_user.role == 'admin' and current_user.area:
                    for record in data:
                        record['area'] = current_user.area
                        record['areaInherited'] = True
                
                # Set status to pending for all preview records
                for record in data:
                    record['status'] = 'pending'
                
                # Return only the first 10 rows for preview
                preview_data = data[:10]
                
                # Add note about automatic house assignment
                return jsonify({
                    "preview": preview_data,
                    "totalRows": len(data),
                    "areaInherited": current_user.role == 'admin' and current_user.area is not None,
                    "autoHouseDistribution": True,
                    "autoHouseDistributionNote": "Students will be automatically and evenly distributed among houses in their area."
                }), 200
            
            # For actual import
            admin_area = None
            if current_user.role == 'admin' and current_user.area:
                admin_area = current_user.area
                
            # For large imports, we need special handling
            is_large_import = len(data) > 200
            
            # Import students with optimized batch processing
            imported_students, errors, summary = import_students_from_file(data, admin_area=admin_area)
            
            # Log import
            AuditLog.log(
                user_id=current_user.id,
                action='import_students',
                details=f"Imported {summary['successful_imports']} students, {summary['failed_imports']} failed",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            # For very large imports, limit the amount of data returned to improve performance
            response_data = {
                "message": f"Import completed. {summary['successful_imports']} students imported successfully, {summary['failed_imports']} failed.",
                "summary": summary,
                "errors": errors[:100] if is_large_import else errors,  # Limit errors for large imports
                "autoHouseDistribution": True,
                "autoHouseDistributionNote": "Students have been automatically and evenly distributed among houses in their area."
            }
            
            if is_large_import:
                # For large imports, don't return the full imported data to keep response size small
                response_data["imported"] = [student.to_dict() for student in imported_students[:50]]
                response_data["importedCount"] = len(imported_students)
                response_data["isLargeImport"] = True
                response_data["noticeMessage"] = "This was a large import. Showing limited results."
            else:
                # For regular imports, return all imported students
                response_data["imported"] = [student.to_dict() for student in imported_students]
            
            return jsonify(response_data), 200
            
        except Exception as e:
            logger.error(f"Error processing import file: {str(e)}")
            return jsonify({"error": f"Error processing file: {str(e)}"}), 400
        
    except Exception as e:
        logger.error(f"Error importing students: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
        
        
@student_api.route('/students/import-template', methods=['GET'])
@jwt_required()
def get_import_template():
    """Get student import template file"""
    try:
        # Check if user is authenticated
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Check if examples should be included
        include_examples = request.args.get('include_examples', 'true').lower() == 'true'
            
        # Create a DataFrame with the template columns
        df = pd.DataFrame(columns=[
            'studentId', 'fullName', 'email', 'phone', 'parentPhone', 
            'address', 'area', 'house', 'notes'
        ])
        
        if include_examples:
            # Add more comprehensive examples
            sample_data = [
                {
                    'studentId': 'SV001', 
                    'fullName': 'Nguyễn Văn A', 
                    'email': 'nguyenvana@example.com',
                    'phone': '0901234567', 
                    'parentPhone': '0987654321',
                    'address': '123 Đường ABC, Quận 1, TP.HCM',
                    'area': 'Khu A',
                    'house': 'Nhà A1',
                    'notes': 'Sinh viên năm nhất ngành CNTT'
                },
                {
                    'studentId': 'SV002', 
                    'fullName': 'Trần Thị B', 
                    'email': 'tranthib@example.com',
                    'phone': '0901234568', 
                    'parentPhone': '0987654322',
                    'address': '456 Đường XYZ, Quận 2, TP.HCM',
                    'area': 'Khu B',
                    'house': 'Nhà B2',
                    'notes': 'Sinh viên năm nhất ngành Kinh tế'
                },
                {
                    'studentId': 'SV003', 
                    'fullName': 'Lê Văn C', 
                    'email': 'levanc@example.com',
                    'phone': '0901234569', 
                    'parentPhone': '0987654323',
                    'address': '789 Đường DEF, Quận 3, TP.HCM',
                    'area': 'Khu C',
                    'house': 'Nhà C3',
                    'notes': 'Sinh viên năm nhất ngành Ngoại ngữ'
                }
            ]
            
            # Add sample data to template
            for row in sample_data:
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        
        # Create Excel file in memory
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # Convert the dataframe to an XlsxWriter Excel object
        df.to_excel(writer, sheet_name='ImportTemplate', index=False)
        
        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['ImportTemplate']
        
        # Add formatting
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'bg_color': '#D9EAD3',
            'border': 1
        })
        
        # Add a note about required fields
        note_format = workbook.add_format({
            'bold': True,
            'font_color': 'red'
        })
        
        # Create instruction format
        instruction_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
        })
        
        # Row offset based on whether examples are included
        row_offset = 3 if include_examples else 0
        
        # Add detailed instructions and guidelines
        worksheet.write(row_offset + 2, 0, 'INSTRUCTIONS FOR IMPORTING STUDENTS:', workbook.add_format({'bold': True, 'font_size': 14}))
        worksheet.write(row_offset + 3, 0, '1. Required fields: studentId, fullName, email, phone, parentPhone, and address are REQUIRED', note_format)
        worksheet.write(row_offset + 4, 0, '2. All students will be imported with PENDING status by default', note_format)
        worksheet.write(row_offset + 5, 0, '3. Area and House fields are optional but recommended for organization', note_format)
        worksheet.write(row_offset + 6, 0, '4. DO NOT change the column headers or the import will fail', note_format)
        worksheet.write(row_offset + 7, 0, '5. For bulk imports, ensure each student has a unique studentId', note_format)
        
        # Add detailed field descriptions
        field_descriptions = [
            {'field': 'studentId', 'desc': 'Unique identifier for the student (ex: SV123, 22AUM12345)'},
            {'field': 'fullName', 'desc': 'Complete name of the student'},
            {'field': 'email', 'desc': 'Valid email address for contact'},
            {'field': 'phone', 'desc': 'Student phone number (should be valid format)'},
            {'field': 'parentPhone', 'desc': "Parent's contact number"},
            {'field': 'address', 'desc': 'Complete physical address'},
            {'field': 'area', 'desc': 'Geographic or organizational area (optional)'},
            {'field': 'house', 'desc': 'Specific house or unit within an area (optional)'},
            {'field': 'notes', 'desc': 'Additional information about the student (optional)'}
        ]
        
        # Add field descriptions worksheet
        fields_sheet = workbook.add_worksheet('Field Descriptions')
        fields_sheet.write(0, 0, 'Field Name', header_format)
        fields_sheet.write(0, 1, 'Description', header_format)
        fields_sheet.write(0, 2, 'Required', header_format)
        fields_sheet.write(0, 3, 'Format Example', header_format)
        
        for i, field in enumerate(field_descriptions, 1):
            fields_sheet.write(i, 0, field['field'])
            fields_sheet.write(i, 1, field['desc'])
            required = field['field'] in ['studentId', 'fullName', 'email', 'phone', 'parentPhone', 'address']
            fields_sheet.write(i, 2, 'YES' if required else 'NO', workbook.add_format({'bold': required}))
            
            # Example format
            if field['field'] == 'studentId':
                fields_sheet.write(i, 3, 'SV123, 22AUM12345')
            elif field['field'] == 'email':
                fields_sheet.write(i, 3, 'example@email.com')
            elif field['field'] == 'phone' or field['field'] == 'parentPhone':
                fields_sheet.write(i, 3, '0901234567')
        
        # Format the header row
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Adjust column widths
        worksheet.set_column('A:A', 15)  # studentId
        worksheet.set_column('B:B', 25)  # fullName
        worksheet.set_column('C:C', 25)  # email
        worksheet.set_column('D:D', 15)  # phone
        worksheet.set_column('E:E', 15)  # parentPhone
        worksheet.set_column('F:F', 35)  # address
        worksheet.set_column('G:G', 15)  # area
        worksheet.set_column('H:H', 15)  # house
        worksheet.set_column('I:I', 30)  # notes
        
        fields_sheet.set_column('A:A', 15)
        fields_sheet.set_column('B:B', 40)
        fields_sheet.set_column('C:C', 10)
        fields_sheet.set_column('D:D', 30)
        
        writer.close()
        output.seek(0)
        
        # Create response with Excel file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='student_import_template.xlsx'
        )
        
    except Exception as e:
        logger.error(f"Error generating template: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@student_api.route('/students/bulk-delete', methods=['POST'])
@jwt_required()
def bulk_delete_students_endpoint():
    """Bulk delete students based on the given IDs"""
    try:
        # Check if user is authenticated and authorized
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
            
        # Admin, root, or mentor can delete students
        if current_user.role.lower() not in ['root', 'admin', 'mentor']:
            return jsonify({"error": "Unauthorized. You don't have permission to perform this action"}), 403
        
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        mode = data.get('mode', 'selected')
        student_ids = data.get('studentIds', [])
        
        # Validate mode
        if mode not in ['all', 'selected']:
            return jsonify({"error": "Invalid mode. Must be 'all' or 'selected'"}), 400
            
        # If mode is 'selected', ensure we have student IDs
        if mode == 'selected' and not student_ids:
            return jsonify({"error": "No student IDs provided for deletion"}), 400
        
        # Track operation statistics
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        # Handle 'all' mode - get all students matching user's area restrictions
        if mode == 'all':
            # For non-root users, restrict to their area
            area_filter = None
            if current_user.role.lower() != 'root' and current_user.area:
                area_filter = current_user.area
                
            # Get IDs of all students that the user can access
            filters = {'area': area_filter} if area_filter else {}
            result = get_all_students(page=1, per_page=sys.maxsize, filters=filters)
            student_ids = [student.id for student in result.get('students', [])]
        
        # Log the bulk delete action
        AuditLog.log(
            user_id=current_user.id,
            action='bulk_delete_students',
            details=f"Bulk delete initiated for {len(student_ids)} students using mode: {mode}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        # Process each student ID
        for student_id in student_ids:
            try:
                # Delete the student - function returns tuple (success_message, error_message)
                success, error = delete_student(student_id)
                if success:
                    success_count += 1
                else:
                    # Log the error and continue with other students
                    logger.error(f"Error deleting student {student_id}: {error}")
                    failed_count += 1
            except Exception as e:
                # Log the error and continue with other students
                logger.error(f"Exception deleting student {student_id}: {str(e)}")
                failed_count += 1
                
        # Return success response with counts
        response_data = {
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "message": f"{success_count} students deleted successfully" if success_count > 0 else "No students were deleted"
        }
        
        # If there were failures, include error message in response
        if failed_count > 0:
            response_data["error"] = f"Failed to delete {failed_count} students"
            
        return jsonify(response_data), 200 if success_count > 0 else 400
            
    except Exception as e:
        logger.error(f"Error in bulk delete students: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@student_api.route('/students/ids', methods=['GET'])
@jwt_required()
def get_student_ids():
    """Get all student IDs matching the current filters (without pagination)"""
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
        logger.info(f"Student ID filters applied: {filters}")
        
        # Import the new function to get all student IDs
        from app.services.student import get_all_student_ids
        student_ids = get_all_student_ids(filters=filters)
        
        # Return all IDs matching the filters
        return jsonify({
            "student_ids": student_ids,
            "count": len(student_ids)
        })
        
    except Exception as e:
        logger.error(f"Error fetching student IDs: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

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
        from app.models.models import User
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

@student_api.route('/students/assign-to-brosis', methods=['POST'])
@jwt_required()
def assign_students_to_brosis():
    """Assign multiple students to a BroSis user"""
    try:
        # Check if user is authenticated and authorized
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
            
        if not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Get data from request
        data = request.json
        if not data or 'brosisId' not in data or 'studentIds' not in data:
            return jsonify({"error": "Missing required fields: brosisId, studentIds"}), 400
        
        brosis_id = data['brosisId']
        student_ids = data['studentIds']
        
        if not isinstance(student_ids, list) or len(student_ids) == 0:
            return jsonify({"error": "studentIds must be a non-empty list"}), 400
        
        # Verify the BroSis user exists and has the correct role
        brosis_user = User.query.get(brosis_id)
        if not brosis_user:
            return jsonify({"error": "BroSis user not found"}), 404
        
        if brosis_user.role != 'brosis':
            return jsonify({"error": "Selected user is not a BroSis"}), 400
        
        # If current user is not root, ensure area restriction
        if current_user.role != 'root' and current_user.area != brosis_user.area:
            return jsonify({"error": "You can only assign students to BroSis users in your area"}), 403
        
        # Process each student
        results = {
            "success": [],
            "failed": []
        }
        
        for student_id in student_ids:
            try:
                student = Student.query.get(student_id)
                
                if not student:
                    results["failed"].append({
                        "id": student_id,
                        "reason": "Student not found"
                    })
                    continue
                
                # Check if student is in the same area as the BroSis
                if student.area != brosis_user.area:
                    results["failed"].append({
                        "id": student_id,
                        "reason": "Student not in the same area as BroSis"
                    })
                    continue
                
                # Check if student is in the same house as the BroSis (if the BroSis has a house)
                if brosis_user.house and student.house != brosis_user.house:
                    results["failed"].append({
                        "id": student_id,
                        "reason": "Student not in the same house as BroSis"
                    })
                    continue
                
                # Assign student to the BroSis
                student.user_id = brosis_user.id
                student.matched = True
                
                # Add to success list
                results["success"].append({
                    "id": student_id,
                    "studentId": student.student_id,
                    "fullName": student.full_name
                })
                
            except Exception as e:
                logger.error(f"Error assigning student {student_id} to BroSis: {str(e)}")
                results["failed"].append({
                    "id": student_id,
                    "reason": str(e)
                })
        
        # Commit changes if any successful assignments
        if results["success"]:
            db.session.commit()
            
            # Log the assignment
            AuditLog.log(
                user_id=current_user.id,
                action='assign_students_to_brosis',
                details=f"Assigned {len(results['success'])} students to BroSis {brosis_user.username}",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
        
        return jsonify({
            "message": f"Successfully assigned {len(results['success'])} students to BroSis {brosis_user.username}",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error in assign_students_to_brosis: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@student_api.route('/students/unassign-from-brosis', methods=['POST'])
@jwt_required()
def unassign_students_from_brosis():
    """Unassign multiple students from a BroSis user"""
    try:
        # Check if user is authenticated and authorized
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
            
        if not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Get data from request
        data = request.json
        if not data or 'studentIds' not in data:
            return jsonify({"error": "Missing required field: studentIds"}), 400
        
        student_ids = data['studentIds']
        
        if not isinstance(student_ids, list) or len(student_ids) == 0:
            return jsonify({"error": "studentIds must be a non-empty list"}), 400
        
        # Process each student
        results = {
            "success": [],
            "failed": []
        }
        
        for student_id in student_ids:
            try:
                student = Student.query.get(student_id)
                
                if not student:
                    results["failed"].append({
                        "id": student_id,
                        "reason": "Student not found"
                    })
                    continue
                
                # Check if the student is actually assigned to a BroSis
                if not student.matched or not student.user_id:
                    results["failed"].append({
                        "id": student_id,
                        "reason": "Student is not assigned to any BroSis"
                    })
                    continue
                
                # Non-root users can only unassign students in their area
                if current_user.role != 'root' and student.area != current_user.area:
                    results["failed"].append({
                        "id": student_id,
                        "reason": "You can only unassign students in your area"
                    })
                    continue
                
                # Record the previous BroSis for logging
                previous_user_id = student.user_id
                previous_user = User.query.get(previous_user_id)
                previous_username = previous_user.username if previous_user else "unknown"
                
                # Unassign student
                student.user_id = None
                student.matched = False
                
                # Add to success list
                results["success"].append({
                    "id": student_id,
                    "studentId": student.student_id,
                    "fullName": student.full_name,
                    "previousBroSis": previous_username
                })
                
            except Exception as e:
                logger.error(f"Error unassigning student {student_id}: {str(e)}")
                results["failed"].append({
                    "id": student_id,
                    "reason": str(e)
                })
        
        # Commit changes if any successful unassignments
        if results["success"]:
            db.session.commit()
            
            # Log the unassignment
            AuditLog.log(
                user_id=current_user.id,
                action='unassign_students_from_brosis',
                details=f"Unassigned {len(results['success'])} students",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
        
        return jsonify({
            "message": f"Successfully unassigned {len(results['success'])} students",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error in unassign_students_from_brosis: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@student_api.route('/students/export-brosis-students', methods=['GET'])
@jwt_required()
def export_brosis_students():
    """Export students assigned to a specific BroSis user"""
    try:
        # Check if user is authenticated and authorized
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Get query parameters
        brosis_id = request.args.get('brosisId')
        format_type = request.args.get('format', 'excel').lower()
        
        if not brosis_id:
            return jsonify({"error": "BroSis ID is required"}), 400
        
        try:
            brosis_id = int(brosis_id)
        except ValueError:
            return jsonify({"error": "Invalid BroSis ID format"}), 400
        
        # Get the BroSis user
        brosis_user = User.query.get(brosis_id)
        if not brosis_user:
            return jsonify({"error": "BroSis user not found"}), 404
        
        if brosis_user.role != 'brosis':
            return jsonify({"error": "Selected user is not a BroSis"}), 400
        
        # Non-root/admin users can only export their own students
        if current_user.role not in ['root', 'admin'] and current_user.id != brosis_id:
            return jsonify({"error": "You can only export your own students"}), 403
        
        # Get all students assigned to this BroSis
        students = Student.query.filter_by(user_id=brosis_id, matched=True).all()
        
        if not students:
            return jsonify({"error": "No students assigned to this BroSis"}), 404
        
        # Prepare data for export
        student_data = []
        for student in students:
            student_data.append({
                'Student ID': student.student_id,
                'Full Name': student.full_name,
                'Email': student.email,
                'Phone': student.phone or '',
                'Area': student.area or '',
                'House': student.house or '',
                'Status': student.status or '',
                'Matched': 'Yes' if student.matched else 'No',
                'Registration Date': student.registration_date.strftime('%Y-%m-%d') if student.registration_date else '',
                'Notes': student.notes or ''
            })
        
        # Create pandas DataFrame
        df = pd.DataFrame(student_data)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        brosis_name = brosis_user.fullName.replace(' ', '_') if brosis_user.fullName else f'brosis_{brosis_id}'
        
        # Export based on format
        if format_type == 'csv':
            # Export as CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            mem_value = output.getvalue()
            
            filename = f"{brosis_name}_students_{timestamp}.csv"
            
            return send_file(
                io.BytesIO(mem_value.encode()),
                mimetype='text/csv',
                download_name=filename,
                as_attachment=True
            )
        else:
            # Export as Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Students', index=False)
                
                # Get the workbook and the worksheet
                workbook = writer.book
                worksheet = writer.sheets['Students']
                
                # Add some formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                # Write the column headers with the defined format
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    
                # Set column widths
                for i, column in enumerate(df.columns):
                    column_width = max(df[column].astype(str).map(len).max(), len(column) + 2)
                    worksheet.set_column(i, i, column_width)
            
            # Get the value from the BytesIO object
            output.seek(0)
            
            filename = f"{brosis_name}_students_{timestamp}.xlsx"
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                download_name=filename,
                as_attachment=True
            )
        
    except Exception as e:
        logger.error(f"Error in export_brosis_students: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@student_api.route('/students/distribute-to-brosis', methods=['POST'])
@jwt_required()
def distribute_students_to_brosis():
    """
    Distribute selected students evenly among brosis users in the same area and house.
    Students will be distributed to ensure each brosis has approximately equal number of students.
    Students without brosis users in their area and house will not be assigned.
    
    Uses Fisher-Yates shuffle to randomize the order of students within each area-house group,
    while still maintaining the load-balancing approach.
    """
    try:
        start_time = time.time()
        # Check if user is authenticated and authorized
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
            
        if not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Get data from request
        data = request.json
        if not data or 'studentIds' not in data:
            return jsonify({"error": "Missing required field: studentIds"}), 400
        
        student_ids = data['studentIds']
        
        if not isinstance(student_ids, list) or len(student_ids) == 0:
            return jsonify({"error": "studentIds must be a non-empty list"}), 400
        
        # Performance optimization: fetch all data we'll need in bulk
        # Fetch all selected students in one query
        students = Student.query.filter(Student.id.in_(student_ids)).all()
        
        if len(students) == 0:
            return jsonify({"error": "No valid students found"}), 404
            
        # Get all active brosis users upfront to avoid multiple queries later
        all_brosis_users = User.query.filter_by(role='brosis', status='active').all()
        
        # Pre-calculate brosis loads for all users
        brosis_loads = {}
        for brosis in all_brosis_users:
            count = Student.query.filter_by(user_id=brosis.id).count()
            if brosis.area and brosis.house:
                key = f"{brosis.area}-{brosis.house}"
                if key not in brosis_loads:
                    brosis_loads[key] = {}
                brosis_loads[key][brosis.id] = {
                    "user": brosis,
                    "current_load": count
                }
        
        # Group students by area and house
        students_by_area_house = {}
        for student in students:
            area = student.area
            house = student.house
            
            # Skip students without area or house
            if not area or not house:
                continue
                
            # Create dict key for area-house pair
            key = f"{area}-{house}"
            
            if key not in students_by_area_house:
                students_by_area_house[key] = []
                
            students_by_area_house[key].append(student)
        
        # Distribution results
        results = {
            "success": [],
            "skipped": []
        }
        
        # Track brosis assignments for reporting
        distribution_counts = {}
        
        # Fisher-Yates shuffle implementation
        def fisher_yates_shuffle(arr):
            """Shuffle array in-place using Fisher-Yates algorithm"""
            import random
            n = len(arr)
            for i in range(n - 1, 0, -1):
                j = random.randint(0, i)
                arr[i], arr[j] = arr[j], arr[i]
            return arr
        
        # Process each area-house group
        for area_house_key, student_group in students_by_area_house.items():
            area, house = area_house_key.split("-", 1)
            
            # Skip if no brosis users found for this area-house
            if area_house_key not in brosis_loads or not brosis_loads[area_house_key]:
                for student in student_group:
                    results["skipped"].append({
                        "id": student.id,
                        "studentId": student.student_id,
                        "fullName": student.full_name,
                        "reason": f"No brosis users found for area '{area}' and house '{house}'"
                    })
                continue
            
            # Apply Fisher-Yates shuffle to randomize the order of students
            # This adds randomization while preserving the area-house grouping
            student_group = fisher_yates_shuffle(student_group)
            
            # Get brosis users for this area-house
            area_house_brosis = brosis_loads[area_house_key]
            
            # Distribute students evenly among brosis users
            for student in student_group:
                # Find brosis with the lowest current assignment count
                min_load_brosis_id = min(
                    area_house_brosis.keys(),
                    key=lambda k: area_house_brosis[k]["current_load"]
                )
                
                # Get the brosis user
                brosis = area_house_brosis[min_load_brosis_id]["user"]
                
                # Assign student to this brosis
                student.user_id = brosis.id
                student.matched = True
                student.user_role = 'brosis'  # Set the role explicitly
                
                # Increment the load for this brosis
                area_house_brosis[min_load_brosis_id]["current_load"] += 1
                
                # Track for distribution counts
                brosis_full_name = brosis.fullName or brosis.username
                if brosis_full_name not in distribution_counts:
                    distribution_counts[brosis_full_name] = 0
                distribution_counts[brosis_full_name] += 1
                
                # Add to success list
                results["success"].append({
                    "id": student.id,
                    "studentId": student.student_id,
                    "fullName": student.full_name,
                    "assignedTo": brosis_full_name
                })
        
        # Commit changes if any successful assignments
        # Use bulk update for better performance with many students
        if results["success"]:
            db.session.commit()
            
            # Log the distribution
            elapsed_time = time.time() - start_time
            AuditLog.log(
                user_id=current_user.id,
                action='distribute_students_to_brosis',
                details=f"Distributed {len(results['success'])} students evenly among brosis users (took {elapsed_time:.2f}s)",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
        
        return jsonify({
            "message": f"Successfully distributed {len(results['success'])} students to brosis users",
            "distribution": distribution_counts,
            "assignedCount": len(results["success"]),
            "skippedCount": len(results["skipped"]),
            "processingTime": f"{(time.time() - start_time):.2f} seconds",
            "results": results
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in distribute_students_to_brosis: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@student_api.route('/students/stats', methods=['GET'])
@jwt_required()
def get_student_statistics():
    """
    Get student statistics - total students, total brosis, assigned students, and average students per brosis.
    """
    try:
        # Check if user is authenticated
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Initialize statistics
        stats = {
            "totalStudents": 0,
            "totalBrosis": 0,
            "assignedStudents": 0,
            "avgStudentsPerBrosis": 0,
            "brosisDistribution": {}
        }
        
        # Apply area restriction for non-root users
        area_filter = None
        if current_user.role != 'root':
            area_filter = current_user.area
        
        # Query to get total students
        students_query = Student.query
        
        # Apply area filter if needed
        if area_filter:
            students_query = students_query.filter_by(area=area_filter)
            
        stats["totalStudents"] = students_query.count()
        
        # Query to get total brosis users
        brosis_query = User.query.filter_by(role='brosis')
        
        # Apply area filter if needed
        if area_filter:
            brosis_query = brosis_query.filter_by(area=area_filter)
            
        # Get active brosis users
        brosis_users = brosis_query.filter_by(status='active').all()
        stats["totalBrosis"] = len(brosis_users)
        
        # Query to get assigned students count
        assigned_query = students_query.filter_by(matched=True)
        stats["assignedStudents"] = assigned_query.count()
        
        # Calculate average students per brosis
        if stats["totalBrosis"] > 0:
            stats["avgStudentsPerBrosis"] = stats["assignedStudents"] / stats["totalBrosis"]
        else:
            stats["avgStudentsPerBrosis"] = 0
        
        # Get distribution of students per brosis by area and house
        # Initialize the distribution dictionary
        stats["brosisDistribution"] = {}
        
        # For each brosis user, count their assigned students
        for brosis in brosis_users:
            area = brosis.area
            house = brosis.house or "Unassigned"
            
            # Initialize area dict if not exists
            if area not in stats["brosisDistribution"]:
                stats["brosisDistribution"][area] = {}
                
            # Initialize house dict if not exists
            if house not in stats["brosisDistribution"][area]:
                stats["brosisDistribution"][area][house] = {}
            
            # Count students for this brosis
            student_count = Student.query.filter_by(user_id=brosis.id).count()
            
            # Add to distribution
            brosis_name = brosis.fullName or brosis.username
            stats["brosisDistribution"][area][house][brosis_name] = student_count
        
        # Return statistics
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error in get_student_statistics: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
