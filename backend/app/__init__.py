from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from app.config.config import Config
from app.models.models import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)
    
    # Enable CORS with additional options to support FormData and file uploads
    CORS(app, 
         resources={r"/api/*": {"origins": "*"}}, 
         supports_credentials=True, 
         methods=["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
         expose_headers=["Content-Disposition", "Content-Length", "Content-Type"],
         allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With", "Origin"])
    
    # Import and register blueprints
    from app.api.routes import api
    from app.api.student_routes import student_api
    from app.api.student_unmap_endpoint import student_api as student_unmap_api
    
    # Đăng ký các blueprint
    # Lưu ý: route '/students' trong routes.py đã bị vô hiệu hóa để tránh xung đột
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(student_api, url_prefix='/api')
    app.register_blueprint(student_unmap_api, url_prefix='/api')
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200
    
    return app
