# User Management System 🚀

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node-v18.x-green.svg)](https://nodejs.org/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-v14+-blue.svg)](https://www.postgresql.org/)
[![React](https://img.shields.io/badge/react-TypeScript-blue.svg)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/flask-latest-lightgrey.svg)](https://flask.palletsprojects.com/)

> 🔐 A comprehensive user management system featuring access control management, 2FA authentication, and complete user data management.

<div align="center">
  <img src="https://user-images.githubusercontent.com/your-username/your-repo/raw/main/docs/assets/banner.png" alt="Project Banner" width="100%">
</div>

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

## 🔑 Key Features

### 👥 User Management
- User registration and authentication
- Profile management
- Role-based access control:
  - 👑 Root
  - 👨‍💼 Admin
  - 👨‍🏫 Mentor
  - 👥 Brosis

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

## 👥 Contributing

We welcome contributions! Here's how you can help:

### 🔄 Repository Setup
```bash
git remote add origin https://github.com/yourusername/your-repo-name.git
git branch -M main
git push -u origin main
```

### 🌟 For Contributors
1. Fork the repository
2. Create your feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Commit your changes
   ```bash
   git commit -m '✨ Add amazing feature'
   ```
4. Push to the branch
   ```bash
   git push origin feature/amazing-feature
   ```
5. Open a Pull Request

### 🔄 Sync Your Fork
```bash
git remote add upstream https://github.com/original-owner/original-repo.git
git fetch upstream
git merge upstream/main
git push origin main
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ by Your Team Name

[Report Bug](https://github.com/yourusername/your-repo-name/issues) · [Request Feature](https://github.com/yourusername/your-repo-name/issues)

</div>