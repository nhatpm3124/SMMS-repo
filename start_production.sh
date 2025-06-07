#!/bin/zsh
# start_production.sh - Script khởi động dự án trong môi trường production
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

# Kiểm tra và dừng các tiến trình đang chạy
check_running_processes() {
  print_header "KIỂM TRA CÁC TIẾN TRÌNH ĐANG CHẠY"
  
  # Dừng các tiến trình frontend
  pkill -f "node.*react-scripts" 2>/dev/null
  pkill -f "serve -s build" 2>/dev/null
  
  # Dừng các tiến trình backend
  pkill -f "python.*run.py" 2>/dev/null
  pkill -f "gunicorn" 2>/dev/null
  
  print_success "Đã dừng các tiến trình đang chạy (nếu có)"
}

# Khởi động backend trong môi trường production
start_backend() {
  print_header "KHỞI ĐỘNG BACKEND"
  
  cd "$BACKEND_DIR" || { print_error "Không thể truy cập thư mục backend!"; exit 1; }
  
  # Kiểm tra môi trường ảo Python
  if [ -d "venv" ]; then
    source venv/bin/activate
  elif [ -d ".venv" ]; then
    source .venv/bin/activate
  else
    print_warning "Không tìm thấy môi trường ảo Python. Đảm bảo đã cài đặt đúng các phụ thuộc!"
  fi
  
  # Kiểm tra phụ thuộc
  pip install -r requirements.txt
  
  # Khởi động backend với Gunicorn trong nền
  print_success "Khởi động backend với Gunicorn..."
  gunicorn -c gunicorn_config.py run:app &
  
  # Kiểm tra nếu backend đã khởi động thành công
  sleep 3
  if pgrep -f "gunicorn" > /dev/null; then
    print_success "Backend đã khởi động thành công"
  else
    print_error "Backend không khởi động được. Kiểm tra logs để biết thêm chi tiết."
    exit 1
  fi
}

# Khởi động frontend trong môi trường production
start_frontend() {
  print_header "KHỞI ĐỘNG FRONTEND"
  
  cd "$FRONTEND_DIR" || { print_error "Không thể truy cập thư mục frontend!"; exit 1; }
  
  # Kiểm tra xem đã build chưa
  if [ ! -d "build" ]; then
    print_warning "Thư mục build không tồn tại. Đang xây dựng frontend..."
    npm run build
  fi
  
  # Cài đặt serve nếu chưa có
  if ! command -v serve &> /dev/null; then
    print_warning "Công cụ 'serve' chưa được cài đặt. Đang cài đặt..."
    npm install -g serve
  fi
  
  # Khởi động frontend trong nền
  print_success "Khởi động frontend..."
  serve -s build &
  
  # Kiểm tra nếu frontend đã khởi động thành công
  sleep 3
  if pgrep -f "serve -s build" > /dev/null; then
    print_success "Frontend đã khởi động thành công"
    echo -e "${GREEN}Ứng dụng web có thể truy cập tại: http://localhost:3000${NC}"
  else
    print_error "Frontend không khởi động được. Kiểm tra logs để biết thêm chi tiết."
  fi
}

# Hiển thị thông tin truy cập
show_access_info() {
  print_header "THÔNG TIN TRUY CẬP"
  
  echo "Frontend: http://localhost:3000"
  echo "Backend API: http://localhost:8000/api"
  
  # Kiểm tra tài khoản root
  cd "$BACKEND_DIR" || { print_error "Không thể truy cập thư mục backend!"; return; }
  
  # Kích hoạt môi trường ảo nếu có
  if [ -d "venv" ]; then
    source venv/bin/activate
  elif [ -d ".venv" ]; then
    source .venv/bin/activate
  fi
  
  echo -e "\n${YELLOW}Thông tin đăng nhập mặc định:${NC}"
  echo "Username: root"
  echo "Password: FpT@707279-hCMcIty"
  echo -e "${YELLOW}Lưu ý: Bạn nên thay đổi mật khẩu mặc định sau khi đăng nhập lần đầu.${NC}"
}

# Hàm chính khởi động dự án
main() {
  print_header "BẮT ĐẦU KHỞI ĐỘNG DỰ ÁN TRONG MÔI TRƯỜNG PRODUCTION"
  
  # Kiểm tra và dừng tiến trình đang chạy
  check_running_processes
  
  # Khởi động backend và frontend
  start_backend
  start_frontend
  
  # Hiển thị thông tin truy cập
  show_access_info
  
  print_success "Dự án đã được khởi động thành công trong môi trường production!"
}

# Thực thi hàm chính
main
