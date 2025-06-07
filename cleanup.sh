#!/bin/zsh
# Project maintenance script
# Usage: ./cleanup.sh [option]
#   Options:
#     clean     - Clean all temporary files (cache, logs)
#     prune     - Remove all debugging tools and test files
#     backup    - Create a backup of the project

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

clean_temp_files() {
  echo "Cleaning temporary files and caches..."
  
  # Clean Python cache files
  find "$PROJECT_DIR/backend" -name "*.pyc" -delete
  find "$PROJECT_DIR/backend" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
  
  # Clean logs
  find "$PROJECT_DIR" -name "*.log" -delete
  
  # Clean .DS_Store files
  find "$PROJECT_DIR" -name ".DS_Store" -delete
  
  echo "Temporary files cleaned successfully."
}

create_backup() {
  echo "Creating project backup..."
  
  BACKUP_DIR="${PROJECT_DIR}_backup_${TIMESTAMP}"
  cp -a "$PROJECT_DIR" "$BACKUP_DIR"
  
  echo "Backup created successfully at: $BACKUP_DIR"
}

prune_debug_files() {
  echo "Removing debug and test files..."
  
  # Backend
  find "$PROJECT_DIR/backend" -name "test_*.py" -delete
  find "$PROJECT_DIR/backend" -name "*debug*" -delete
  find "$PROJECT_DIR/backend" -name "*.new" -delete
  
  # Frontend
  find "$PROJECT_DIR/frontend/src" -name "*debug*" -delete
  find "$PROJECT_DIR/frontend" -name "fix-*.sh" -delete
  
  echo "Debug and test files removed successfully."
}

case "$1" in
  "clean")
    clean_temp_files
    ;;
  "prune")
    prune_debug_files
    ;;
  "backup")
    create_backup
    ;;
  *)
    echo "Project Maintenance Tool"
    echo "Usage: ./cleanup.sh [option]"
    echo "Options:"
    echo "  clean     - Clean all temporary files (cache, logs)"
    echo "  prune     - Remove all debugging tools and test files"
    echo "  backup    - Create a backup of the project"
    ;;
esac
BACKUP_DIR="/Users/nhatpm/Desktop/project_backup_$(date +%Y%m%d_%H%M%S)"
echo "Creating backup at: $BACKUP_DIR"
cp -a "/Users/nhatpm/Desktop/project" "$BACKUP_DIR"

# 1. Clean root directory - Remove testing scripts and duplicate docs
echo "Cleaning root directory..."
# Remove test scripts
rm -f /Users/nhatpm/Desktop/project/test_*.js
rm -f /Users/nhatpm/Desktop/project/test_*.sh
rm -f /Users/nhatpm/Desktop/project/test_import_format.txt

# Remove tool scripts that are no longer needed
rm -f /Users/nhatpm/Desktop/project/check_all_errors.sh
rm -f /Users/nhatpm/Desktop/project/clean_project.sh
rm -f /Users/nhatpm/Desktop/project/pre_deploy.sh
rm -f /Users/nhatpm/Desktop/project/restart_servers.sh

# Organize documentation - move useful docs to docs directory
mkdir -p /Users/nhatpm/Desktop/project/docs/guides
mkdir -p /Users/nhatpm/Desktop/project/docs/troubleshooting
mkdir -p /Users/nhatpm/Desktop/project/docs/security

# Move relevant documentation files to appropriate directories
for file in /Users/nhatpm/Desktop/project/*.md; do
  if [ "$file" != "/Users/nhatpm/Desktop/project/README.md" ]; then
    # Move security docs
    if [[ "$file" == *"ROOT_USER"* || "$file" == *"2FA"* || "$file" == *"SECURITY"* ]]; then
      mv "$file" /Users/nhatpm/Desktop/project/docs/security/
    # Move troubleshooting docs
    elif [[ "$file" == *"TROUBLESHOOTING"* || "$file" == *"FIX"* || "$file" == *"DEBUG"* ]]; then
      mv "$file" /Users/nhatpm/Desktop/project/docs/troubleshooting/
    # Move other guides
    else
      mv "$file" /Users/nhatpm/Desktop/project/docs/guides/
    fi
  fi
done

# 2. Clean backend directory
echo "Cleaning backend directory..."
# Remove test files
find /Users/nhatpm/Desktop/project/backend -name "test_*.py" -delete

# Remove debug and utility scripts
find /Users/nhatpm/Desktop/project/backend -name "*_debug.py" -delete
find /Users/nhatpm/Desktop/project/backend -name "check_*.py" -delete
find /Users/nhatpm/Desktop/project/backend -name "fix_*.py" -delete
find /Users/nhatpm/Desktop/project/backend -name "verify_*.py" -delete
find /Users/nhatpm/Desktop/project/backend -name "*.log" -delete

# Remove setup scripts
find /Users/nhatpm/Desktop/project/backend -name "setup_*.sh" -delete
find /Users/nhatpm/Desktop/project/backend -name "setup_*.py" -delete
find /Users/nhatpm/Desktop/project/backend -name "init_*.py" -delete
find /Users/nhatpm/Desktop/project/backend -name "cleanup_*.sh" -delete

# Remove unnecessary QR code images and tools
rm -f /Users/nhatpm/Desktop/project/backend/root_2fa_qr.png
rm -f /Users/nhatpm/Desktop/project/backend/get_root_2fa_code.py

# Remove Python cache
find /Users/nhatpm/Desktop/project/backend -name "__pycache__" -type d -exec rm -rf {} +
find /Users/nhatpm/Desktop/project/backend -name "*.pyc" -delete

# 3. Clean frontend directory
echo "Cleaning frontend directory..."
# Remove fix and debug scripts
rm -f /Users/nhatpm/Desktop/project/frontend/fix-*.sh
rm -f /Users/nhatpm/Desktop/project/frontend/check-deps.js
rm -f /Users/nhatpm/Desktop/project/frontend/cleanup_frontend_debug.sh

# Remove debug files and test files
find /Users/nhatpm/Desktop/project/frontend/src -name "*debug*" -delete
find /Users/nhatpm/Desktop/project/frontend/src -name "*test*" -delete

# Remove .vscode directory if it exists
rm -rf /Users/nhatpm/Desktop/project/frontend/.vscode

echo "Cleanup completed successfully!"
echo "Backup is available at: $BACKUP_DIR"
