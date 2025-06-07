# User Import Guide

This guide explains how to import multiple users into the system using Excel files.

## Overview

The system allows administrators to import multiple users at once using an Excel file. This is useful for onboarding large groups of users efficiently.

## Excel File Format

Your Excel file should include the following columns:

### Required Columns:
- **fullName**: User's full name
- **email**: User's email address

### For BroSis Users:
- **studentId**: Student ID (required for users with role "brosis")
- **username**: Optional for BroSis users - will be auto-generated if not provided

### For Admin and Mentor Users:
- **username**: Required for admin and mentor roles

### Optional Columns:
- **phone**: User's phone number
- **area**: User's area
- **house**: User's house
- **role**: User role, must be one of: "admin", "mentor", "brosis" (default is "brosis")
- **status**: User status, must be one of: "active", "inactive" (default is "active")

## Import Process

1. Log in with administrator privileges
2. Navigate to the User Management section
3. Click on "Import Users" tab or button
4. Download the template file (if needed)
5. Fill in your user data in the Excel template
6. Upload the completed file
7. Review the import results

## Notes

- Usernames must be unique in the system
- Email addresses must be unique in the system
- For BroSis users, the studentId field is mandatory
- For BroSis users, username will be auto-generated from fullName and studentId if not provided
  - Auto-generated usernames follow the pattern: `firstName + initials + studentId`
  - Example: "Phạm Minh Nhật" with ID "SE182965" → username = "nhatpmse182965"
- Area values must match existing areas in the system (not case-sensitive)
- House values must match existing houses within the specified area (not case-sensitive)
- Role values must be one of: admin, mentor, brosis (not case-sensitive)
- If area is specified but house is not, the user will be assigned to the area without a specific house
- If house is specified, area must also be provided, and the house must belong to that area
- Passwords will be set to the same value as the username initially (users will be prompted to change on first login)
- For security reasons, users with "root" role cannot be imported this way
- The system will validate each row and provide specific error messages for any issues

## Error Handling

The import results page provides detailed information about any errors encountered during import:

### Error Types

1. **Area Errors**: Indicates that an area name doesn't match any existing area in the system
   - The error message will show all valid area names
   - Example: "Invalid Area: 'FPT HCM'. Please use one of the valid areas: Hoa Lac, Da Nang, Can Tho, Quy Nhon"

2. **House Errors**: Indicates that a house name doesn't match any existing house in the specified area
   - The error message will show all valid houses for the specified area
   - Example: "Invalid House: 'House B' does not exist in Area 'Hoa Lac'. Valid houses for this area are: Alpha, Beta, Gamma"

3. **Other Errors**: Various other validation errors
   - Duplicate username/email: "Username already exists" / "Email already exists"
   - Missing required fields: "Student ID is required for BroSis users"

### Using the Error Filter

You can filter the error list by type to focus on specific issues:
- Use the "All Errors" button to see all errors
- Use the "Area Errors" button to focus on area-related issues
- Use the "House Errors" button to focus on house-related issues
- Use the "Other Errors" button to see remaining validation issues

## Sample Excel File

| username | fullName | email | phone | area | house | role | status | studentId |
|----------|----------|-------|-------|------|-------|------|--------|-----------|
| user1 | User One | user1@example.com | 1234567890 | Area A | House 1 | brosis | active | SE123456 |
| user2 | User Two | user2@example.com | 0987654321 | Area B | House 2 | mentor | active | SE234567 |
| user3 | User Three | user3@example.com | 5551234567 | Area C | House 3 | admin | inactive | SE345678 |

## Troubleshooting

### Common Issues:

1. **Missing Required Fields**
   - Make sure all required columns are present
   - For BroSis users, studentId is required

2. **Duplicate Users**
   - Username or email already exists in the system
   - Each username and email must be unique

3. **Invalid Role or Status**
   - Role must be one of: "admin", "mentor", "brosis"
   - Status must be one of: "active", "inactive"

4. **Invalid Area or House**
   - Area must match an existing area in the system
   - House must match an existing house within the specified area
   - Example: If "Ho Chi Minh" is a valid area but "Unicorn" is not a house in that area, the import will fail

5. **File Format Issues**
   - Only .xlsx and .xls formats are supported
   - Make sure column names match exactly those listed above
