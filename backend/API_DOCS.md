# API Documentation

This file contains documentation for the API endpoints of the backend service.

## Authentication Endpoints

- POST /api/auth/login - User login
- POST /api/auth/register - User registration
- POST /api/auth/verify-2fa - Verify 2FA code
- POST /api/auth/setup-2fa - Set up 2FA for user

## User Management Endpoints

- GET /api/users - Get users list (with pagination and filtering)
- POST /api/users - Create a new user
- GET /api/users/:id - Get user by ID
- PUT /api/users/:id - Update user by ID
- DELETE /api/users/:id - Delete user by ID
- POST /api/users/bulk-status - Change status for multiple users
- POST /api/users/bulk-delete - Delete multiple users
- POST /api/users/import - Import users from Excel file
- POST /api/users/export - Export users to Excel or CSV format

## Area and House Endpoints

- GET /api/areas - Get all areas
- GET /api/houses - Get all houses
- GET /api/areas-houses - Get areas and houses mapping