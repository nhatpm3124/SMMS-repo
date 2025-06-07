from typing import List, Dict, Any
import pandas as pd
from io import BytesIO
from flask import send_file
from app.models.models import User, db
from sqlalchemy import or_

def generate_export_file(mode: str, format: str = 'excel', user_ids: List[int] = None, filters: Dict = None) -> Dict[str, Any]:
    """
    Generate an export file (Excel or CSV) for users based on mode and filters
    Args:
        mode: 'all' or 'selected'
        format: 'excel' or 'csv' 
        user_ids: List of user IDs when mode is 'selected'
        filters: Dictionary of filters to apply (search, role, status, area, house)
    Returns:
        Dictionary with:
        - file_obj: BytesIO object containing the file data
        - filename: Suggested filename for the download
        - mimetype: Appropriate mimetype for the response
    """
    try:
        # Build the query based on mode and filters
        query = User.query
        
        # Always exclude root users from export
        query = query.filter(User.role != 'root')
        
        if mode == 'selected' and user_ids:
            # Filter for specific user IDs
            query = query.filter(User.id.in_(user_ids))
            
        # Apply additional filters if provided
        if filters:
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term),
                    User.fullName.ilike(search_term),
                    User.phone.ilike(search_term),
                    User.area.ilike(search_term),
                    User.house.ilike(search_term),
                    User.student_id.ilike(search_term)
                ))
            
            if filters.get('role'):
                query = query.filter(User.role == filters['role'])
                
            if filters.get('status'):
                query = query.filter(User.status == filters['status'])
                
            if filters.get('area'):
                query = query.filter(User.area == filters['area'])
                
            if filters.get('house'):
                query = query.filter(User.house == filters['house'])
            
        # Execute query and get users
        users = query.all()
        
        # Prepare data for export
        data = []
        for user in users:
            user_data = {
                'Username': user.username,
                'Full Name': user.fullName,
                'Email': user.email,
                'Phone': user.phone or '',
                'Area': user.area or '',
                'House': user.house or '',
                'Role': user.role,
                'Status': user.status,
                'Student ID': user.student_id or ''
            }
            data.append(user_data)
            
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create file object
        file_obj = BytesIO()
        
        # Generate export datetime for filename
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        if format.lower() == 'csv':
            # Export as CSV
            df.to_csv(file_obj, index=False, encoding='utf-8-sig')
            mimetype = 'text/csv'
            filename = f'users-export-{timestamp}.csv'
        else:
            # Export as Excel
            df.to_excel(file_obj, index=False, engine='openpyxl')
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'users-export-{timestamp}.xlsx'
            
        # Reset file pointer to beginning
        file_obj.seek(0)
        
        return {
            'file_obj': file_obj,
            'filename': filename,
            'mimetype': mimetype
        }
        
    except Exception as e:
        import traceback
        print(f"Error generating export file: {str(e)}")
        print(traceback.format_exc())
        raise
