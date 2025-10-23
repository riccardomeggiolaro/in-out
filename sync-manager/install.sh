#!/bin/bash

##############################################################################
# Sync Manager - Installation Script
# Installs and configures the Sync Manager service
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
INSTALL_DIR="/opt/sync-manager"
SERVICE_USER="syncmanager"
VENV_DIR="$INSTALL_DIR/venv"
CONFIG_DIR="/etc/sync-manager"
DATA_DIR="/var/lib/sync-manager"
LOG_DIR="/var/log/sync-manager"
SYSTEMD_SERVICE="/etc/systemd/system/sync-manager.service"

# Functions
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   Sync Manager Installation                               ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
    fi
}

check_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
        print_info "Detected OS: $PRETTY_NAME"
    else
        print_error "Cannot detect OS"
    fi
}

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_info "Python version: $PYTHON_VERSION"
        
        # Check minimum version (3.8)
        REQUIRED_VERSION="3.8"
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
            print_error "Python 3.8 or higher is required"
        fi
    else
        print_error "Python 3 is not installed"
    fi
}

install_dependencies() {
    print_info "Installing system dependencies..."
    
    case "$OS" in
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y -qq \
                python3-pip \
                python3-venv \
                python3-dev \
                build-essential \
                rsync \
                git \
                curl \
                supervisor \
                nginx \
                certbot \
                python3-certbot-nginx
            ;;
        centos|rhel|fedora)
            yum install -y \
                python3-pip \
                python3-devel \
                gcc \
                rsync \
                git \
                curl \
                supervisor \
                nginx \
                certbot \
                python3-certbot-nginx
            ;;
        *)
            print_error "Unsupported OS: $OS"
            ;;
    esac
    
    print_success "System dependencies installed"
}

create_user() {
    print_info "Creating service user..."
    
    if id "$SERVICE_USER" &>/dev/null; then
        print_warning "User $SERVICE_USER already exists"
    else
        useradd -r -s /bin/false -d "$DATA_DIR" "$SERVICE_USER"
        print_success "User $SERVICE_USER created"
    fi
}

create_directories() {
    print_info "Creating directories..."
    
    # Create directories
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    
    # Set permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$CONFIG_DIR"
    chmod 755 "$DATA_DIR"
    chmod 755 "$LOG_DIR"
    
    print_success "Directories created"
}

install_application() {
    print_info "Installing application..."
    
    # Copy application files
    if [[ -d "./app" ]]; then
        cp -r ./* "$INSTALL_DIR/"
    else
        # Clone from repository
        print_info "Cloning from repository..."
        git clone https://github.com/yourusername/sync-manager.git "$INSTALL_DIR"
    fi
    
    # Create virtual environment
    print_info "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
    
    # Activate virtual environment and install dependencies
    print_info "Installing Python dependencies..."
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install -r "$INSTALL_DIR/requirements.txt"
    deactivate
    
    # Set permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    print_success "Application installed"
}

configure_application() {
    print_info "Configuring application..."
    
    # Create configuration file
    cat > "$CONFIG_DIR/config.yaml" <<EOF
# Sync Manager Configuration
server:
  host: 0.0.0.0
  port: 8000
  workers: 4

database:
  url: sqlite+aiosqlite:///$DATA_DIR/sync_manager.db

logging:
  level: INFO
  file: $LOG_DIR/sync_manager.log
  max_size: 10485760
  backup_count: 5

paths:
  data_dir: $DATA_DIR
  temp_dir: /tmp/sync_manager

security:
  secret_key: $(openssl rand -hex 32)
  api_key_enabled: true
  api_key: $(openssl rand -hex 16)
EOF
    
    # Create .env file
    cat > "$INSTALL_DIR/.env" <<EOF
CONFIG_FILE=$CONFIG_DIR/config.yaml
DATA_DIR=$DATA_DIR
LOG_FILE=$LOG_DIR/sync_manager.log
EOF
    
    # Set permissions
    chmod 600 "$CONFIG_DIR/config.yaml"
    chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR/config.yaml"
    
    print_success "Application configured"
}

create_systemd_service() {
    print_info "Creating systemd service..."
    
    cat > "$SYSTEMD_SERVICE" <<EOF
[Unit]
Description=Sync Manager Service
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="PYTHONPATH=$INSTALL_DIR"
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/sync_manager.log
StandardError=append:$LOG_DIR/sync_manager_error.log

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR $LOG_DIR /mnt

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    print_success "Systemd service created"
}

configure_nginx() {
    print_info "Configuring Nginx..."
    
    # Backup default configuration
    if [[ -f /etc/nginx/sites-enabled/default ]]; then
        mv /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.bak
    fi
    
    # Create Nginx configuration
    cat > /etc/nginx/sites-available/sync-manager <<'EOF'
server {
    listen 80;
    server_name _;
    
    # Redirect to HTTPS
    # return 301 https://$server_name$request_uri;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# HTTPS configuration (uncomment after running certbot)
# server {
#     listen 443 ssl http2;
#     server_name your-domain.com;
#     
#     ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
#     
#     # ... rest of configuration ...
# }
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/sync-manager /etc/nginx/sites-enabled/
    
    # Test configuration
    nginx -t
    
    # Reload Nginx
    systemctl reload nginx
    
    print_success "Nginx configured"
}

setup_firewall() {
    print_info "Setting up firewall..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 8000/tcp
        ufw --force enable
        print_success "UFW firewall configured"
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --permanent --add-port=8000/tcp
        firewall-cmd --reload
        print_success "Firewalld configured"
    else
        print_warning "No firewall found"
    fi
}

initialize_database() {
    print_info "Initializing database..."
    
    source "$VENV_DIR/bin/activate"
    cd "$INSTALL_DIR"
    
    # Run database migrations
    python -c "
import asyncio
from app.core.database import init_db
asyncio.run(init_db())
"
    
    deactivate
    
    # Set permissions
    chown "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR/sync_manager.db"
    
    print_success "Database initialized"
}

start_service() {
    print_info "Starting service..."
    
    systemctl enable sync-manager
    systemctl start sync-manager
    
    # Wait for service to start
    sleep 3
    
    if systemctl is-active --quiet sync-manager; then
        print_success "Service started successfully"
    else
        print_error "Service failed to start. Check logs: journalctl -u sync-manager"
    fi
}

print_summary() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   Installation Complete!                                   ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Service Information:"
    echo "  • Status: $(systemctl is-active sync-manager)"
    echo "  • URL: http://$(hostname -I | awk '{print $1}'):8000"
    echo "  • API Docs: http://$(hostname -I | awk '{print $1}'):8000/docs"
    echo "  • Config: $CONFIG_DIR/config.yaml"
    echo "  • Logs: $LOG_DIR/sync_manager.log"
    echo ""
    
    # Get API key from config
    API_KEY=$(grep "api_key:" "$CONFIG_DIR/config.yaml" | tail -1 | awk '{print $2}')
    echo "API Key: $API_KEY"
    echo ""
    echo "Commands:"
    echo "  • Start:   systemctl start sync-manager"
    echo "  • Stop:    systemctl stop sync-manager"
    echo "  • Status:  systemctl status sync-manager"
    echo "  • Logs:    journalctl -u sync-manager -f"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure your sync paths in the web interface"
    echo "  2. Set up SSL certificate: certbot --nginx -d your-domain.com"
    echo "  3. Configure backup strategy for $DATA_DIR"
    echo ""
}

# Main installation flow
main() {
    print_header
    
    # Pre-flight checks
    check_root
    check_os
    check_python
    
    # Installation
    install_dependencies
    create_user
    create_directories
    install_application
    configure_application
    create_systemd_service
    configure_nginx
    setup_firewall
    initialize_database
    start_service
    
    # Summary
    print_summary
}

# Handle errors
trap 'print_error "Installation failed at line $LINENO"' ERR

# Run main function
main "$@"
