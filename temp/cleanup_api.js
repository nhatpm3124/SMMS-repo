const fs = require('fs');
const path = require('path');

// Read the API service file
const apiServicePath = path.join('/Users/nhatpm/Desktop/project/frontend/src/services/api.ts');
let content = fs.readFileSync(apiServicePath, 'utf8');

// Remove student-related interface types
content = content.replace(/interface BulkStudentOperationPayload \{[\s\S]*?studentIds: number\[\]; \/\/ Empty array when mode is 'all'\n\}\n\n/g, '');
content = content.replace(/interface BulkStudentStatusChangePayload extends BulkStudentOperationPayload \{[\s\S]*?\}\n\n/g, '');

// Remove studentId field from UserData interface
content = content.replace(/  studentId\?: string; \/\/ Added for BroSis users\n/g, '');

// Remove studentId field from UserUpdateData interface
content = content.replace(/  studentId\?: string;\n/g, '');

// Remove student-related API methods (getStudents, createStudent, etc.)
[
  // Get all students
  /\/\/ Get all students \(protected\)[\s\S]*?return \{ error: 'Network error, please try again' \};\n  \},\n\n/g,
  
  // Create student
  /\/\/ Create a new student \(protected\)[\s\S]*?return \{ error: `Network error: \${error\.message \|\| 'Failed to connect to server'}\` \};\n    \}\n  \},\n\n/g,
  
  // Update student
  /\/\/ Update a student \(protected\)[\s\S]*?return \{ error: `Network error: \${error\.message \|\| 'Failed to connect to server'}\` \};\n    \}\n  \},\n\n/g,
  
  // Toggle student status
  /\/\/ Toggle student status \(protected\)[\s\S]*?return \{ error: `Network error: \${error\.message \|\| 'Failed to connect to server'}\` \};\n    \}\n  \},\n\n/g,
  
  // Bulk change student status
  /\/\/ Bulk change status for students \(protected\)[\s\S]*?return \{ error: `Network error: \${error\.message \|\| 'Failed to connect to server'}\` \};\n    \}\n  \},\n\n/g,
  
  // Bulk delete students
  /\/\/ Bulk delete students \(protected\)[\s\S]*?return \{ error: `Network error: \${error\.message \|\| 'Failed to connect to server'}\` \};\n    \}\n  \},\n\n/g,
  
  // Delete student
  /\/\/ Delete a student \(protected\)[\s\S]*?return \{ error: `Network error: \${error\.message \|\| 'Failed to connect to server'}\` \};\n    \}\n  \},\n\n/g,
  
  // Import students
  /\/\/ Import students from Excel\/CSV file \(protected\)[\s\S]*?return \{ error: `Network error: \${error\.message \|\| 'Failed to connect to server'}\` \};\n    \}\n  \},\n\n/g,
  
  // Export students
  /\/\/ Export students to CSV\/Excel \(protected\)[\s\S]*?return \{ error: `Network error: \${error\.message \|\| 'Failed to connect to server'}\` \};\n    \}\n  \},\n\n/g,
  
  // Get import template
  /\/\/ Get import template for students \(protected\)[\s\S]*?return `\${API_BASE_URL}\/students\/import-template\?format=\${format}`;\n    \}\n  \},\n\n/g
].forEach(pattern => {
  content = content.replace(pattern, '');
});

// Write the cleaned content back
fs.writeFileSync('/Users/nhatpm/Desktop/project/temp/api_clean.ts', content);
console.log('API service cleaned and written to temp file');
