const fs = require('fs');
const path = require('path');

// Read the original API service file
const apiServicePath = path.join('/Users/nhatpm/Desktop/project/frontend/src/services/api.ts');
const content = fs.readFileSync(apiServicePath, 'utf8');

// List of student-related methods to be removed
const methodsToRemove = [
  'getStudents',
  'createStudent',
  'updateStudent',
  'toggleStudentStatus',
  'bulkChangeStudentStatus',
  'bulkDeleteStudents',
  'deleteStudent', 
  'importStudents',
  'exportStudents',
  'getImportTemplate'
];

// Split the file into lines
const lines = content.split('\n');
let cleanedContent = [];
let insideStudentMethod = false;
let braceCounter = 0;

// Remove studentId from interfaces
for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  
  // Remove studentId from UserData interface
  if (line.includes('studentId?: string;') && (line.includes('// Added for BroSis users') || line.includes('// For BroSis users'))) {
    continue;
  }
  
  // Skip BulkStudentOperationPayload interface
  if (line.includes('interface BulkStudentOperationPayload')) {
    // Skip lines until we reach the closing bracket
    while (i < lines.length && !lines[i].match(/^\}$/)) {
      i++;
    }
    i++; // Skip the closing bracket too
    continue;
  }
  
  // Skip BulkStudentStatusChangePayload interface
  if (line.includes('interface BulkStudentStatusChangePayload')) {
    // Skip lines until we reach the closing bracket
    while (i < lines.length && !lines[i].match(/^\}$/)) {
      i++;
    }
    i++; // Skip the closing bracket too
    continue;
  }
  
  // Check if line starts a student method
  const methodMatch = line.match(/^\s+(\/\/ .* student.*|getStudents:|createStudent:|updateStudent:|toggleStudentStatus:|bulkChangeStudentStatus:|bulkDeleteStudents:|deleteStudent:|importStudents:|exportStudents:|getImportTemplate:)/i);
  
  if (methodMatch) {
    insideStudentMethod = true;
    braceCounter = 0;
    continue;
  }
  
  // Count braces when inside a method
  if (insideStudentMethod) {
    // Count opening braces
    const openBraces = (line.match(/{/g) || []).length;
    braceCounter += openBraces;
    
    // Count closing braces
    const closeBraces = (line.match(/}/g) || []).length;
    braceCounter -= closeBraces;
    
    // If braceCounter is 0 and we found a comma or a method ends, we're out of the method
    if (braceCounter === 0 && (line.trim() === '},')) {
      insideStudentMethod = false;
      continue;
    }
    
    // Skip all lines while inside the method
    continue;
  }
  
  // Add the line to cleaned content if not in a student method
  cleanedContent.push(line);
}

// Write cleaned content back to the file
fs.writeFileSync('/Users/nhatpm/Desktop/project/temp/api_direct_clean.ts', cleanedContent.join('\n'));
console.log('API service directly cleaned and written to temp file');
