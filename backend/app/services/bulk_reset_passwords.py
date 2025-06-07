"""
Bulk password reset for multiple users at once
"""
from app.models.models import db, User, AuditLog
from flask import request

def bulk_reset_passwords(mode, user_ids, current_user_id):
    """
    Reset passwords for multiple users at once
    
    Args:
        mode (str): 'all' to reset all non-protected users or 'selected' to reset specific users
        user_ids (list): List of user IDs to reset when mode is 'selected'
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
            # Reset all non-protected users
            query = User.query
            
            # CRITICAL SECURITY: ALWAYS exclude root users from bulk operations, regardless of current user's role
            # Since is_protected_user is a Python property and not a column, we need to use individual filters
            query = query.filter(User.role != 'root')  # Exclude by role (main method)
            query = query.filter(User.is_root != True)  # Exclude by is_root flag (legacy backup)
            
            # Additional protection: filter out common admin usernames as a last resort
            query = query.filter(~User.username.in_(['root', 'admin', 'superadmin', 'administrator']))
            
            # Log this protection for audit purposes
            AuditLog.log(
                user_id=current_user_id,
                action='root_user_protection',
                details=f"Bulk password reset automatically excluded all root users",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            # Reset passwords in a batch for efficiency
            try:
                users_to_reset = query.all()
                for user in users_to_reset:
                    # Reset password to username
                    user.set_password(user.username)
                    # Set flag to require password change on next login
                    user.password_change_required = True
                
                db.session.commit()
                success_count = len(users_to_reset)
                
                # Create audit log entry
                user_agent = request.headers.get('User-Agent', '')
                ip = request.remote_addr
                
                AuditLog.log(
                    user_id=current_user_id,
                    action='bulk_reset_passwords',
                    details=f"Bulk reset passwords for {success_count} users with mode 'all'",
                    ip_address=ip,
                    user_agent=user_agent
                )
            except Exception as e:
                db.session.rollback()
                failed_count = query.count()
                
                # Log the error
                print(f"Error during bulk password reset: {str(e)}")
                
                # Create audit log entry for failed operation
                user_agent = request.headers.get('User-Agent', '')
                ip = request.remote_addr
                
                AuditLog.log(
                    user_id=current_user_id,
                    action='bulk_reset_passwords_failed',
                    details=f"Failed to bulk reset passwords for {failed_count} users with error: {str(e)}",
                    ip_address=ip,
                    user_agent=user_agent
                )
        else:
            # Reset passwords only for selected users
            for user_id in user_ids:
                try:
                    user = User.query.get(user_id)
                    
                    if not user:
                        skipped_count += 1
                        continue
                    
                    # CRITICAL SECURITY: ALWAYS skip root users regardless of selection
                    if user.is_protected_user:
                        skipped_count += 1
                        # Log this skipped operation for security audit 
                        AuditLog.log(
                            user_id=current_user_id,
                            action='root_user_protection',
                            details=f"Protected root user {user.username} (ID: {user.id}) from bulk password reset",
                            ip_address=request.remote_addr,
                            user_agent=request.headers.get('User-Agent', '')
                        )
                        continue
                    
                    # Reset the password to username
                    user.set_password(user.username)
                    # Set flag to require password change on next login
                    user.password_change_required = True
                    db.session.commit()
                    success_count += 1
                    
                    # Create individual audit log entry
                    user_agent = request.headers.get('User-Agent', '')
                    ip = request.remote_addr
                    
                    AuditLog.log(
                        user_id=current_user_id,
                        action='reset_password_in_bulk',
                        details=f"Reset password for {user.username} (ID: {user_id}) as part of bulk operation",
                        ip_address=ip,
                        user_agent=user_agent
                    )
                    
                except Exception as e:
                    db.session.rollback()
                    failed_count += 1
                    print(f"Error resetting password for user ID {user_id}: {str(e)}")
        
        # Create a summary audit log
        user_agent = request.headers.get('User-Agent', '')
        ip = request.remote_addr
        
        AuditLog.log(
            user_id=current_user_id,
            action='bulk_reset_passwords_summary',
            details=f"Bulk password reset operation completed: {success_count} successful, {failed_count} failed, {skipped_count} skipped",
            ip_address=ip,
            user_agent=user_agent
        )
        
        return {
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count
        }
        
    except Exception as e:
        print(f"Unexpected error in bulk_reset_passwords: {str(e)}")
        return {
            "success": success_count,
            "failed": failed_count + (len(user_ids) - success_count - skipped_count if mode == 'selected' else 0),
            "skipped": skipped_count,
            "error": str(e)
        }
