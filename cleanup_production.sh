#!/bin/zsh
# cleanup_production.sh - Dọn dẹp dự án cho môi trường production
# Tác giả: GitHub Copilot
# Ngày: $(date +"%d/%m/%Y")

# Màu sắc cho terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Đường dẫn dự án
PROJECT_DIR="/Users/nhatpm/Desktop/project"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/Users/nhatpm/Desktop/project_backup_${TIMESTAMP}"

# Hàm hiển thị tiêu đề
print_header() {
  echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Hàm hiển thị thông báo thành công
print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

# Hàm hiển thị cảnh báo
print_warning() {
  echo -e "${YELLOW}⚠️ $1${NC}"
}

# Hàm hiển thị lỗi
print_error() {
  echo -e "${RED}❌ $1${NC}"
}

# Tạo bản sao lưu
create_backup() {
  print_header "TẠO BẢN SAO LƯU"
  echo "Tạo bản sao lưu tại: $BACKUP_DIR"
  cp -a "$PROJECT_DIR" "$BACKUP_DIR"
  print_success "Đã tạo bản sao lưu thành công!"
}

# Dọn dẹp thư mục gốc
clean_root_directory() {
  print_header "DỌN DẸP THƯ MỤC GỐC"
  
  # Xóa file script test và không cần thiết
  echo "Đang xóa các script test và không cần thiết..."
  find "$PROJECT_DIR" -maxdepth 1 -name "test_*.js" -delete
  find "$PROJECT_DIR" -maxdepth 1 -name "test_*.sh" -delete
  find "$PROJECT_DIR" -maxdepth 1 -name "test_*.py" -delete
  find "$PROJECT_DIR" -maxdepth 1 -name "debug_*.sh" -delete
  find "$PROJECT_DIR" -maxdepth 1 -name "debug_*.js" -delete
  find "$PROJECT_DIR" -maxdepth 1 -name "fix_*.sh" -delete
  find "$PROJECT_DIR" -maxdepth 1 -name "check_*.sh" -delete
  find "$PROJECT_DIR" -maxdepth 1 -name "clean_*.sh" -delete
  find "$PROJECT_DIR" -maxdepth 1 -name "verify_*.sh" -delete
  
  # Để lại các script quan trọng
  # - start_project.sh (script khởi động dự án)
  # - cleanup.sh (script dọn dẹp tạm thời)
  
  print_success "Đã dọn dẹp thư mục gốc thành công!"
}

# Dọn dẹp thư mục backend
clean_backend_directory() {
  print_header "DỌN DẸP BACKEND"
  
  echo "Đang xóa các file test và debug..."
  # Xóa file test
  find "$BACKEND_DIR" -name "test_*.py" -delete
  
  # Xóa file debug và các script utility
  find "$BACKEND_DIR" -name "*_debug.py" -delete
  find "$BACKEND_DIR" -name "debug_*.py" -delete
  find "$BACKEND_DIR" -name "check_*.py" -delete
  find "$BACKEND_DIR" -name "fix_*.py" -delete
  find "$BACKEND_DIR" -name "verify_*.py" -delete
  find "$BACKEND_DIR" -name "*.log" -delete
  
  # Xóa script setup, init, cleanup không cần thiết
  find "$BACKEND_DIR" -name "setup_*.sh" -delete
  find "$BACKEND_DIR" -name "setup_*.py" -delete
  find "$BACKEND_DIR" -name "init_*.py" -delete
  find "$BACKEND_DIR" -name "cleanup_*.sh" -delete
  
  # Xóa file QR code tạm thời
  rm -f "$BACKEND_DIR/root_2fa_qr.png"
  
  # Xóa cache Python
  find "$BACKEND_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
  find "$BACKEND_DIR" -name "*.pyc" -delete
  
  print_success "Đã dọn dẹp backend thành công!"
}

# Dọn dẹp thư mục frontend
clean_frontend_directory() {
  print_header "DỌN DẸP FRONTEND"
  
  echo "Đang xóa các file test và debug..."
  # Xóa các script fix và debug
  rm -f "$FRONTEND_DIR/fix-"*.sh
  rm -f "$FRONTEND_DIR/debug-"*.sh
  rm -f "$FRONTEND_DIR/check-"*.js
  rm -f "$FRONTEND_DIR/cleanup_"*.sh
  
  # Xóa thư mục và file test
  find "$FRONTEND_DIR/src" -name "*debug*" -delete
  find "$FRONTEND_DIR/src" -name "*.test.*" -delete
  find "$FRONTEND_DIR/src" -name "__tests__" -type d -exec rm -rf {} + 2>/dev/null || true
  
  # Xóa các file cấu hình IDE
  rm -rf "$FRONTEND_DIR/.vscode"
  
  # Xóa các file tạm
  find "$FRONTEND_DIR" -name ".DS_Store" -delete
  find "$FRONTEND_DIR" -name "*.log" -delete
  
  print_success "Đã dọn dẹp frontend thành công!"
}

# Xây dựng frontend cho production
build_frontend_production() {
  print_header "XÂY DỰNG FRONTEND CHO PRODUCTION"
  
  echo "Đang xây dựng frontend cho production..."
  cd "$FRONTEND_DIR" || { print_error "Không thể truy cập thư mục frontend!"; exit 1; }
  
  # Kiểm tra và tạo thư mục styles nếu chưa tồn tại
  if [ ! -d "$FRONTEND_DIR/src/styles" ]; then
    mkdir -p "$FRONTEND_DIR/src/styles"
    print_warning "Đã tạo thư mục styles thiếu"
  fi
  
  # Tạo file checkbox-fix.css nếu chưa tồn tại
  if [ ! -f "$FRONTEND_DIR/src/styles/checkbox-fix.css" ]; then
    echo "/* Custom checkbox styling fixes */
.custom-checkbox {
  appearance: none;
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border: 1px solid #ccc;
  border-radius: 4px;
  outline: none;
  cursor: pointer;
  position: relative;
  background-color: white;
}

.custom-checkbox:checked {
  background-color: #4a90e2;
  border-color: #4a90e2;
}

.custom-checkbox:checked::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 6px;
  width: 5px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.custom-checkbox:focus {
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.25);
}" > "$FRONTEND_DIR/src/styles/checkbox-fix.css"
    print_warning "Đã tạo file checkbox-fix.css thiếu"
  fi
  
  # Xây dựng frontend cho production
  npm run build
  
  print_success "Đã xây dựng frontend thành công!"
}

# Chuẩn bị backend cho production
prepare_backend_production() {
  print_header "CHUẨN BỊ BACKEND CHO PRODUCTION"
  
  echo "Đang chuẩn bị backend cho production..."
  cd "$BACKEND_DIR" || { print_error "Không thể truy cập thư mục backend!"; exit 1; }
  
  # Kiểm tra môi trường ảo Python
  if [ -d "venv" ]; then
    source venv/bin/activate
  elif [ -d ".venv" ]; then
    source .venv/bin/activate
  else
    print_warning "Không tìm thấy môi trường ảo Python. Đảm bảo đã cài đặt đúng các phụ thuộc!"
  fi
  
  # Kiểm tra các phụ thuộc production cần thiết
  echo "Kiểm tra phụ thuộc production..."
  pip install -r requirements.txt
  
  # Xóa các phụ thuộc phát triển không cần thiết
  # python -m pip uninstall -y pytest pytest-cov coverage
  
  print_success "Đã chuẩn bị backend thành công!"
}

# Hàm chính thực hiện dọn dẹp
main() {
  print_header "BẮT ĐẦU QUÁ TRÌNH DỌN DẸP CHO PRODUCTION"
  
  # Tạo bản sao lưu
  create_backup
  
  # Dọn dẹp các thư mục
  clean_root_directory
  clean_backend_directory
  clean_frontend_directory
  
  # Chuẩn bị cho production
  build_frontend_production
  prepare_backend_production
  
  print_header "HOÀN THÀNH DỌN DẸP CHO PRODUCTION"
  echo -e "${GREEN}Dự án đã được dọn dẹp thành công và sẵn sàng cho production!${NC}"
  echo -e "${YELLOW}Bản sao lưu có sẵn tại: ${BACKUP_DIR}${NC}"
  echo "Để khởi động dự án, sử dụng lệnh: ./start_project.sh"
}

# Hiển thị cảnh báo trước khi chạy
echo -e "${YELLOW}CẢNH BÁO: Quá trình này sẽ xóa các file test, debug và không cần thiết khỏi dự án.${NC}"
echo -e "${YELLOW}Một bản sao lưu sẽ được tạo tại: ${BACKUP_DIR}${NC}"

# Thực thi hàm chính
main
