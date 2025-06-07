from flask_sqlalchemy import SQLAlchemy
import hashlib
import os
import argon2
from datetime import datetime
import pyotp

db = SQLAlchemy()

class Area(db.Model):
    """Area model for representing geographical locations like cities"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    # Relationship with houses
    houses = db.relationship('House', backref='area', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

class House(db.Model):
    """House model for representing buildings or locations within an area"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'areaId': self.area_id
        }

class User(db.Model):
    """User model for authentication and authorization"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    fullName = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    area = db.Column(db.String(100), nullable=True)
    house = db.Column(db.String(100), nullable=True)
    student_id = db.Column(db.String(20), nullable=True) # Student ID for BroSis users
    password_hash = db.Column(db.String(256))  # Password hash storage
    
    # The following fields might not exist in older databases
    # Using nullable=True and ensuring our code checks for None values
    is_admin = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='active')
    
    # New fields that might not exist yet
    # We'll handle these in the code if they're missing
    hash_type = db.Column(db.String(20), nullable=True)
    is_root = db.Column(db.Boolean, nullable=True)
    role = db.Column(db.String(20), default='BroSis', nullable=True)  # 'root', 'admin', 'mentor', 'brosis'
    two_factor_secret = db.Column(db.String(32), nullable=True)
    two_factor_enabled = db.Column(db.Boolean, nullable=True)
    password_change_required = db.Column(db.Boolean, default=True)  # Default to True so normal users must change initial password
    
    def set_password(self, password, hash_type="sha256"):
        """
        Set the password using the specified hashing algorithm
        - sha256: Default hashing (backward compatible)
        - argon2id: Advanced hashing for root user
        """
        self.hash_type = hash_type
        
        if hash_type == "argon2id":
            # Use Argon2id for stronger security (for root user)
            hasher = argon2.PasswordHasher(
                time_cost=3,  # Number of iterations
                memory_cost=65536,  # Memory usage in kibibytes
                parallelism=4,  # Number of parallel threads
                hash_len=32,  # Length of the hash in bytes
                salt_len=16,  # Length of the salt in bytes
                encoding='utf-8',  # The encoding of the password
                type=argon2.Type.ID  # The Argon2 variant to use
            )
            self.password_hash = hasher.hash(password)
        else:
            # Simple password hashing using sha256 (default for backward compatibility)
            salt = os.urandom(32)
            self.password_hash = hashlib.sha256(salt + password.encode()).hexdigest() + ':' + salt.hex()
        
    def check_password(self, password):
        if not self.password_hash:
            return False
        
        # Check which hashing algorithm was used
        hash_type = getattr(self, 'hash_type', 'sha256')  # Default to sha256 if attribute doesn't exist
        
        if hash_type == "argon2id":
            # Argon2id verification
            try:
                hasher = argon2.PasswordHasher()
                hasher.verify(self.password_hash, password)
                return True
            except argon2.exceptions.VerifyMismatchError:
                return False
            except Exception:
                return False
        else:
            # Simple password verification with SHA-256 (default)
            try:
                stored_hash, salt_hex = self.password_hash.split(':')
                salt = bytes.fromhex(salt_hex)
                calculated_hash = hashlib.sha256(salt + password.encode()).hexdigest()
                return stored_hash == calculated_hash
            except Exception:
                return False
    
    def setup_2fa(self):
        """Set up 2FA for the user"""
        if not self.two_factor_secret:
            # Generate a random secret key
            self.two_factor_secret = pyotp.random_base32()
        return self.two_factor_secret
    
    def get_2fa_uri(self, app_name="FPTApp"):
        """Get the 2FA provisioning URI"""
        return pyotp.totp.TOTP(self.two_factor_secret).provisioning_uri(
            name=self.email, 
            issuer_name=app_name
        )
    
    def verify_2fa(self, token):
        """Verify a 2FA token"""
        if not self.two_factor_enabled or not self.two_factor_secret:
            return False
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(token)
    
    def enable_2fa(self):
        """Enable 2FA for user"""
        if self.two_factor_secret:
            self.two_factor_enabled = True
            return True
        return False
    
    def disable_2fa(self):
        """Disable 2FA for user"""
        self.two_factor_enabled = False
        return True
    
    @property
    def is_protected_user(self):
        """
        Determines if this is a protected user (root user) that should never be affected by bulk operations
        
        This property combines multiple checks for maximum security:
        1. Checks the role field (modern approach)
        2. Checks the is_root flag (legacy approach)
        3. Uses a username-based fallback for very old databases
        
        Returns:
            bool: True if this user is a protected root user, False otherwise
        """
        # Primary check: role-based (modern approach)
        if hasattr(self, 'role') and self.role == 'root':
            return True
        
        # Secondary check: boolean flag (legacy approach)
        if hasattr(self, 'is_root') and self.is_root:
            return True
            
        # Fallback check: for very old databases that might not have proper role fields
        if self.username and self.username.lower() in ['root', 'admin', 'superadmin', 'administrator']:
            return True
            
        return False
    
    def to_dict(self):
        """Convert user object to dictionary for API responses"""
        # Use the new role field if available, otherwise calculate from is_root/is_admin for compatibility
        role = getattr(self, 'role', None)
        if not role:
            role = "root" if self.is_root else ("admin" if self.is_admin else "brosis")
            
        data = {
            'id': self.id,
            'username': self.username,
            'fullName': self.fullName,
            'email': self.email,
            'phone': self.phone,
            'area': self.area,
            'house': self.house,
            'role': role,
            'status': self.status,
            'two_factor_enabled': self.two_factor_enabled,
            'password_change_required': getattr(self, 'password_change_required', True)  # Default to True if not present
        }
        
        # Include student_id if it exists and role is brosis
        if role.lower() == 'brosis' and hasattr(self, 'student_id') and self.student_id:
            data['studentId'] = self.student_id
            
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'


class AuditLog(db.Model):
    """Model for tracking user actions for audit purposes"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100), nullable=False)  # e.g., "create_user", "delete_user"
    details = db.Column(db.Text, nullable=True)  # JSON or text description of the action
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    
    # Create relationship with User model
    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))
    
    @classmethod
    def log(cls, user_id, action, details=None, ip_address=None, user_agent=None):
        """Create an audit log entry"""
        log_entry = cls(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    def __repr__(self):
        return f'<AuditLog {self.id} - {self.action}>'

class Group(db.Model):
    """Model for mentor-managed student groups"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key to the mentor who owns this group
    mentor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship to the mentor (User)
    mentor = db.relationship('User', foreign_keys=[mentor_id], backref=db.backref('managed_groups', lazy=True))
    
    # Foreign key to leader (a BroSis user who is designated as leader)
    leader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationship to the leader (User)
    leader = db.relationship('User', foreign_keys=[leader_id], backref=db.backref('leading_groups', lazy=True))
    
    # Area and house - needed to enforce that groups belong to specific areas/houses
    area = db.Column(db.String(100), nullable=False)
    house = db.Column(db.String(100), nullable=False)
    
    # Group members (many-to-many relationship with User through GroupMember)
    members = db.relationship('GroupMember', back_populates='group', cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'mentor_id': self.mentor_id,
            'leader_id': self.leader_id,
            'area': self.area,
            'house': self.house,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'members': [member.to_dict() for member in self.members]
        }
    
    def __repr__(self):
        return f'<Group {self.name}>'

class GroupMember(db.Model):
    """Many-to-many association table between Group and User"""
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    group = db.relationship('Group', back_populates='members')
    user = db.relationship('User', backref=db.backref('group_memberships', lazy=True))
    
    # Every user can only be in a group once
    __table_args__ = (db.UniqueConstraint('group_id', 'user_id', name='_group_user_uc'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'user': self.user.to_dict() if self.user else None
        }
    
    def __repr__(self):
        return f'<GroupMember {self.id}>'
