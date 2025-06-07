# User Management System 🚀

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node-v18.x-green.svg)](https://nodejs.org/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-v14+-blue.svg)](https://www.postgresql.org/)
[![React](https://img.shields.io/badge/react-TypeScript-blue.svg)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/flask-latest-lightgrey.svg)](https://flask.palletsprojects.com/)

> 🔐 A comprehensive user management system featuring access control management, 2FA authentication, and complete user data management.


## ✨ Features Highlights

- 👥 **Advanced User Management**
- 🔒 **Two-Factor Authentication (2FA)**
- 🏢 **Hierarchical Organization Structure**
- 📊 **Bulk Data Operations**
- 🛡️ **Enterprise-grade Security**

## 🏗️ Architecture

The project follows a modern microservices architecture:

### 🎨 Frontend
- React with TypeScript
- Tailwind CSS for styling
- Modern and responsive UI
- State management with Redux

### ⚙️ Backend
- Flask REST API
- SQLAlchemy ORM
- JWT Authentication
- PostgreSQL/SQLite database

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:

| Requirement | Version |
|------------|---------|
| Node.js    | ≥ 18.x  |
| Python     | ≥ 3.9   |
| PostgreSQL | ≥ 14.x  |
| npm/yarn   | Latest  |

### 🔧 Installation

1. **Clone & Navigate**
   ```bash
   git clone <repository-url>
   cd project
   ```

2. **Set Up Backend** 🐍
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set Up Frontend** ⚛️
   ```bash
   cd ../frontend
   npm install
   ```

4. **Configure Database** 🗄️
   ```bash
   cd ../backend
   ./setup_postgres.sh   # For PostgreSQL
   # OR
   ./setup_sqlite.sh     # For SQLite (Development)
   ```

5. **Initialize Database** 
   ```bash
   python init_db.py
   ```

## 🚀 Launch Application

### One-Click Launch
```bash
./start_project.sh
```

### Manual Launch

<details>
<summary>Click to expand manual launch steps</summary>

1. **Start Backend**
   ```bash
   cd backend
   source venv/bin/activate
   python run.py
   ```

2. **Start Frontend**
   ```bash
   cd frontend
   npm start
   ```
</details>



### 🔒 Security Features
- JWT Authentication
- Password encryption
- Two-Factor Authentication (2FA)
- Account lockout protection
- Session management

### 📊 Data Management
- Bulk user import/export
- Excel/CSV support
- Data validation
- Audit logging

## 📚 Documentation

Comprehensive documentation available in the `docs` directory:

| Guide | Description |
|-------|-------------|
| [📘 Deployment Guide](docs/guides/DEPLOYMENT_GUIDE.md) | Step-by-step deployment instructions |
| [🔧 Database Troubleshooting](docs/troubleshooting/DATABASE_TROUBLESHOOTING.md) | Database-related issues and solutions |
| [🔑 JWT Token Guide](docs/troubleshooting/JWT_TOKEN_TROUBLESHOOTING.md) | Authentication troubleshooting |
| [📥 User Import Guide](docs/USER_IMPORT_GUIDE.md) | Bulk user import instructions |
| [📤 User Export Guide](docs/guides/USER_EXPORT_GUIDE.md) | Data export procedures |

## 🚀 Production Deployment

### Cleanup & Optimization
```bash
./cleanup_production.sh
```

### Production Launch
```bash
./start_production.sh
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ by Dottrip Industries


</div>
