from app.models.models import db
from datetime import datetime

class Student(db.Model):
    """Student model for representing students in the system"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)  # Student ID
    full_name = db.Column(db.String(100), nullable=False)  # Full name
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)  # Required field
    parent_phone = db.Column(db.String(20), nullable=False)  # Parent's phone number
    address = db.Column(db.String(255), nullable=False)  # Student's address
    area = db.Column(db.String(100), nullable=True)  # Area name 
    house = db.Column(db.String(100), nullable=True)  # House name
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=True)  # Area ID
    house_id = db.Column(db.Integer, db.ForeignKey('house.id'), nullable=True)  # House ID
    status = db.Column(db.String(20), default='active')  # 'active' or 'inactive'
    matched = db.Column(db.Boolean, default=False)  # Whether assigned to a mentor/brosis
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # User ID of assigned mentor/brosis
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    assigned_user = db.relationship('User', backref='assigned_students', lazy=True)
    area_relation = db.relationship('Area', backref='students', lazy=True)
    house_relation = db.relationship('House', backref='students', lazy=True)
    
    def to_dict(self):
        """Convert student object to dictionary for API responses"""
        return {
            'id': self.id,
            'studentId': self.student_id,
            'fullName': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'parentPhone': self.parent_phone,
            'address': self.address,
            'area': self.area,
            'house': self.house,
            'areaId': self.area_id,
            'houseId': self.house_id,
            'status': self.status,
            'matched': self.matched,
            'userId': self.user_id,
            'userFullName': self.assigned_user.fullName if self.assigned_user else None,
            'userRole': self.assigned_user.role if self.assigned_user else None,
            'registrationDate': self.registration_date.isoformat(),
            'notes': self.notes
        }
    
    def __repr__(self):
        return f'<Student {self.student_id}>'
