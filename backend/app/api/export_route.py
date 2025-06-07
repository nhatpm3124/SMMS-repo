from flask import jsonify, request, send_file
from flask_jwt_extended import jwt_required
from app.api import api
from app.services.auth import get_current_user
from app.models.models import AuditLog
from app.services.export import generate_export_file
import traceback

@api.route('/users/export', methods=['GET'])
@jwt_required()
def export_users():
    try:
        current_user = get_current_user()
        
        if not current_user or not (current_user.role in ['admin', 'root']):
            return jsonify({"error": "Admin privileges required"}), 403
        
        mode = request.args.get('mode', 'all')
        if mode not in ['all', 'selected']:
            return jsonify({"error": "Invalid mode. Must be 'all' or 'selected'"}), 400
            
        format = request.args.get('format', 'excel')
        if format not in ['excel', 'csv']:
            return jsonify({"error": "Invalid format. Must be 'excel' or 'csv'"}), 400
            
        user_ids = []
        if mode == 'selected':
            user_ids_str = request.args.get('userIds')
            if not user_ids_str:
                return jsonify({"error": "User IDs required for selected mode"}), 400
            try:
                user_ids = [int(id) for id in user_ids_str.split(',')]
            except ValueError:
                return jsonify({"error": "Invalid user IDs format"}), 400
                
        filters = {}
        
        search = request.args.get('search')
        if search:
            filters['search'] = search
        
        role = request.args.get('role')
        if role and role != 'all':
            filters['role'] = role.lower()
        
        status = request.args.get('status')
        if status and status != 'all':
            filters['status'] = status.lower()
        
        area = request.args.get('area') 
        if area and area != 'all':
            filters['area'] = area
        
        house = request.args.get('house')
        if house:
            filters['house'] = house
        
        result = generate_export_file(mode=mode, format=format, user_ids=user_ids, filters=filters)
        
        filter_text = ""
        if filters:
            filter_text = f" with filters: {filters}"
            
        details = f"Exported {mode} users to {format} format"
        if mode == 'selected':
            details += f" ({len(user_ids)} users)"
        details += filter_text
            
        AuditLog.log(
            user_id=current_user.id,
            action='export_users',
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        return send_file(
            result['file_obj'],
            mimetype=result['mimetype'],
            as_attachment=True,
            download_name=result['filename']
        )
        
    except Exception as e:
        print(f"Error exporting users: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500
