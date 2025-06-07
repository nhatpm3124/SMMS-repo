"""
Bulk operations for users management
"""

from app.models.models import db, User, AuditLog
from flask import request

# Import the bulk reset passwords function
from app.services.bulk_reset_passwords import bulk_reset_passwords

def bulk_delete_users(mode, user_ids, current_user_id):
    """
    Delete multiple users at once
    
    Args:
        mode (str): 'all' to delete all non-protected users or 'selected' to delete specific users
        user_ids (list): List of user IDs to delete when mode is 'selected'
        current_user_id (int): ID of the current user performing the operation
        
    Returns:
        dict: Results with success, failed, and skipped counts
    """
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    try:
        # Get current user for protection checks
        current_user = User.query.get(current_user_id)
        if not current_user:
            return {
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "error": "Current user not found"
            }
        
        if mode == 'all':
            # Delete all non-protected users
            # Protected users: root users, the current user, and any other admin users if the current user is not root
            
            # CRITICAL SECURITY: ALWAYS exclude root users by BOTH role and is_root flag
            query = User.query
            
            # First priority exclusion - filter out root users
            query = query.filter(User.role != 'root')  # Exclude by role
            query = query.filter(User.is_root != True)  # Exclude by is_root flag for backwards compatibility
            
            # Secondary exclusions
            query = query.filter(User.id != current_user_id)  # Exclude current user
            
            # If current user is not root, also exclude admin users
            if current_user.role != 'root':
                query = query.filter(User.role != 'admin')
                
            # Get total count for logging
            total_to_delete = query.count()
            
            # Get user IDs for deletion
            users_to_delete = query.all()
            user_ids_to_delete = [user.id for user in users_to_delete]
            
            # Log all users being deleted for audit purposes
            usernames_to_delete = [user.username for user in users_to_delete]
            
            # Use a batch approach for efficient deletion
            user_details = []
            for user in users_to_delete:
                user_details.append(f"{user.username} (ID: {user.id})")
            
            # Delete users in batches
            try:
                for user in users_to_delete:
                    db.session.delete(user)
                db.session.commit()
                success_count = len(user_ids_to_delete)
                
                # Create audit log entry for bulk deletion
                user_agent = request.headers.get('User-Agent', '')
                ip = request.remote_addr
                
                AuditLog.log(
                    user_id=current_user_id,
                    action='bulk_delete_users',
                    details=f"Bulk deleted {success_count} users with mode 'all'",
                    ip_address=ip,
                    user_agent=user_agent
                )
            except Exception as e:
                db.session.rollback()
                failed_count = len(user_ids_to_delete)
                
                # Log the error
                print(f"Error during bulk delete: {str(e)}")
                
                # Create audit log entry for failed operation
                user_agent = request.headers.get('User-Agent', '')
                ip = request.remote_addr
                
                AuditLog.log(
                    user_id=current_user_id,
                    action='bulk_delete_users_failed',
                    details=f"Failed to bulk delete {failed_count} users with error: {str(e)}",
                    ip_address=ip,
                    user_agent=user_agent
                )
        else:
            # Delete only selected users
            for user_id in user_ids:
                try:
                    user = User.query.get(user_id)
                    
                    if not user:
                        skipped_count += 1
                        continue
                    
                    # CRITICAL SECURITY: ALWAYS skip root users regardless of selection
                    # Use the comprehensive is_protected_user property for maximum security
                    if user.is_protected_user:
                        skipped_count += 1
                        # Log this skipped operation for security audit 
                        AuditLog.log(
                            user_id=current_user_id,
                            action='root_user_protection',
                            details=f"Protected root user {user.username} (ID: {user.id}) from bulk deletion",
                            ip_address=request.remote_addr,
                            user_agent=request.headers.get('User-Agent', '')
                        )
                        continue
                    
                    # Skip current user (self)
                    if str(user.id) == str(current_user_id):
                        skipped_count += 1
                        continue
                    
                    # Skip admin users if current user is not root
                    if user.role == 'admin' and current_user.role != 'root':
                        skipped_count += 1
                        continue
                    
                    # Store username for audit log
                    username = user.username
                    
                    # Delete the user
                    db.session.delete(user)
                    db.session.commit()
                    success_count += 1
                    
                    # Create individual audit log entry
                    user_agent = request.headers.get('User-Agent', '')
                    ip = request.remote_addr
                    
                    AuditLog.log(
                        user_id=current_user_id,
                        action='delete_user_in_bulk',
                        details=f"Deleted user: {username} (ID: {user_id}) as part of bulk operation",
                        ip_address=ip,
                        user_agent=user_agent
                    )
                    
                except Exception as e:
                    db.session.rollback()
                    failed_count += 1
                    print(f"Error deleting user ID {user_id}: {str(e)}")
        
        # Create a summary audit log
        user_agent = request.headers.get('User-Agent', '')
        ip = request.remote_addr
        
        AuditLog.log(
            user_id=current_user_id,
            action='bulk_delete_summary',
            details=f"Bulk delete operation completed: {success_count} successful, {failed_count} failed, {skipped_count} skipped",
            ip_address=ip,
            user_agent=user_agent
        )
        
        return {
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count
        }
        
    except Exception as e:
        print(f"Unexpected error in bulk_delete_users: {str(e)}")
        return {
            "success": success_count,
            "failed": failed_count + (len(user_ids) - success_count - skipped_count),
            "skipped": skipped_count,
            "error": str(e)
        }

def bulk_change_status(mode, user_ids, action, current_user_id):
    """
    Change status for multiple users at once
    
    Args:
        mode (str): 'all' to change all non-protected users or 'selected' to change specific users
        user_ids (list): List of user IDs to modify when mode is 'selected'
        action (str): 'activate' or 'deactivate' to set the corresponding status
        current_user_id (int): ID of the current user performing the operation
        
    Returns:
        dict: Results with success, failed, and skipped counts
    """
    # Implementation for bulk status change
    # (Similar to bulk_delete_users but updating status instead of deleting)
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    new_status = 'active' if action == 'activate' else 'inactive'
    
    try:
        # Get current user for protection checks
        current_user = User.query.get(current_user_id)
        if not current_user:
            return {
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "error": "Current user not found"
            }
        
        if mode == 'all':
            # Change status for all non-protected users
            query = User.query
            
            # CRITICAL SECURITY: ALWAYS exclude root users from bulk operations, regardless of current user's role
            # First priority exclusion - filter out root users using multiple checks
            
            # Since is_protected_user is a Python property and not a column, we need to use individual filters
            query = query.filter(User.role != 'root')  # Exclude by role (main method)
            query = query.filter(User.is_root != True)  # Exclude by is_root flag (legacy backup)
            
            # Additional protection: filter out common admin usernames as a last resort
            query = query.filter(~User.username.in_(['root', 'admin', 'superadmin', 'administrator']))
            
            # Log this protection for audit purposes
            AuditLog.log(
                user_id=current_user_id,
                action='root_user_protection',
                details=f"Bulk status change automatically excluded all root users",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            # Skip users that already have the target status
            query = query.filter(User.status != new_status)
            
            # Get total count for logging
            total_to_change = query.count()
            
            # Update status in a single query for efficiency
            try:
                users_to_update = query.all()
                for user in users_to_update:
                    user.status = new_status
                
                db.session.commit()
                success_count = total_to_change
                
                # Create audit log entry
                user_agent = request.headers.get('User-Agent', '')
                ip = request.remote_addr
                
                AuditLog.log(
                    user_id=current_user_id,
                    action=f'bulk_{action}_users',
                    details=f"Bulk {action}d {success_count} users with mode 'all'",
                    ip_address=ip,
                    user_agent=user_agent
                )
            except Exception as e:
                db.session.rollback()
                failed_count = total_to_change
                
                # Log the error
                print(f"Error during bulk status change: {str(e)}")
                
                # Create audit log entry for failed operation
                user_agent = request.headers.get('User-Agent', '')
                ip = request.remote_addr
                
                AuditLog.log(
                    user_id=current_user_id,
                    action=f'bulk_{action}_users_failed',
                    details=f"Failed to bulk {action} {failed_count} users with error: {str(e)}",
                    ip_address=ip,
                    user_agent=user_agent
                )
        else:
            # Change status only for selected users
            for user_id in user_ids:
                try:
                    user = User.query.get(user_id)
                    
                    if not user:
                        skipped_count += 1
                        continue
                    
                    # Skip users that already have the target status
                    if user.status == new_status:
                        skipped_count += 1
                        continue
                    
                    # CRITICAL SECURITY: ALWAYS skip root users regardless of selection
                    # Use the comprehensive is_protected_user property for maximum security
                    if user.is_protected_user:
                        skipped_count += 1
                        # Log this skipped operation for security audit 
                        AuditLog.log(
                            user_id=current_user_id,
                            action='root_user_protection',
                            details=f"Protected root user {user.username} (ID: {user.id}) from bulk status change",
                            ip_address=request.remote_addr,
                            user_agent=request.headers.get('User-Agent', '')
                        )
                        continue
                    
                    # Update the status
                    old_status = user.status
                    user.status = new_status
                    db.session.commit()
                    success_count += 1
                    
                    # Create individual audit log entry
                    user_agent = request.headers.get('User-Agent', '')
                    ip = request.remote_addr
                    
                    AuditLog.log(
                        user_id=current_user_id,
                        action=f'change_user_status_in_bulk',
                        details=f"Changed {user.username}'s status from {old_status} to {new_status} (ID: {user_id}) as part of bulk operation",
                        ip_address=ip,
                        user_agent=user_agent
                    )
                    
                except Exception as e:
                    db.session.rollback()
                    failed_count += 1
                    print(f"Error changing status for user ID {user_id}: {str(e)}")
        
        # Create a summary audit log
        user_agent = request.headers.get('User-Agent', '')
        ip = request.remote_addr
        
        AuditLog.log(
            user_id=current_user_id,
            action=f'bulk_{action}_summary',
            details=f"Bulk {action} operation completed: {success_count} successful, {failed_count} failed, {skipped_count} skipped",
            ip_address=ip,
            user_agent=user_agent
        )
        
        return {
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count
        }
        
    except Exception as e:
        print(f"Unexpected error in bulk_change_status: {str(e)}")
        return {
            "success": success_count,
            "failed": failed_count + (len(user_ids) - success_count - skipped_count),
            "skipped": skipped_count,
            "error": str(e)
        }