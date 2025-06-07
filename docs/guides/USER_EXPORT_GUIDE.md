# User Export Functionality

## Overview
This document describes the user export functionality for the project's user management interface. The export feature allows administrators to export user data in different formats (Excel, CSV) for reporting, backup, or data analysis purposes.

## Feature Description
The user export functionality enables administrators to export user data in two formats:
- Excel (.xlsx) format
- CSV (.csv) format

The export can be performed based on:
- Currently selected users on the page
- All users in the system (excluding root users)

## Implementation Details

### Frontend Components
1. **Export Button**: Added next to the "Import Users" button in the UserManagement component
2. **Format Selection Dropdown**: Allows the user to choose between Excel and CSV formats
3. **Export Status Tracking**: Shows loading state during export and handles success/error messages

### API Integration
The frontend uses the `ApiService.exportUsers()` method which:
- Takes parameters for export mode (all or selected users), user IDs, and format
- Makes a POST request to `/api/users/export` with the appropriate payload
- Handles the binary file response and triggers browser download

### Backend Requirements
The backend API endpoint `/api/users/export` should:
- Accept a JSON payload specifying export mode, user IDs, and format
- Support filtering by user IDs when in 'selected' mode
- Generate the appropriate file format (Excel or CSV)
- Return the file as a downloadable attachment
- Include appropriate headers (Content-Disposition, Content-Type)

## Payload Structure
```typescript
interface ExportUsersPayload {
  mode: 'all' | 'selected';
  userIds: number[];  // Used when mode is 'selected'
  format: 'csv' | 'excel';  // Default is 'excel' if not specified
}
```

## Response Headers
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet (for Excel)
Content-Type: text/csv (for CSV)
Content-Disposition: attachment; filename="users-export-YYYY-MM-DD.xlsx"
```

## User Experience Flow
1. The user selects users on the page (optional)
2. The user selects the export format from the dropdown (Excel or CSV)
3. The user clicks the Export button
4. A loading spinner appears during the export process
5. Upon successful export, the file is automatically downloaded to the user's device
6. A success message is displayed briefly
7. If an error occurs, an error message is displayed

## Security Considerations
- Only administrative users should have access to the export functionality
- Personal identifiable information should be handled according to privacy regulations
- Rate limiting should be implemented to prevent abuse
