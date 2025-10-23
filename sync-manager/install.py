#!/usr/bin/env python3
"""
Sync Manager Installation Script
"""

import os
import sys
import shutil
import secrets
import subprocess
from pathlib import Path
import platform
import getpass


class Colors:
    """Terminal colors for output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")


def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required. Current version: {sys.version}")
        return False
    print_success(f"Python version: {sys.version.split()[0]}")
    return True


def check_system():
    """Check system compatibility"""
    system = platform.system()
    if system not in ["Linux", "Darwin", "Windows"]:
        print_warning(f"Untested system: {system}")
    else:
        print_success(f"System: {system}")
    
    # Check if running in Docker
    if Path("/.dockerenv").exists():
        print_info("Running in Docker container")
    
    return True


def check_dependencies():
    """Check system dependencies"""
    dependencies = {
        "rsync": "rsync --version",
        "git": "git --version",
    }
    
    missing = []
    for dep, cmd in dependencies.items():
        try:
            subprocess.run(cmd.split(), capture_output=True, check=True)
            print_success(f"Found: {dep}")
        except:
            missing.append(dep)
            print_warning(f"Missing: {dep}")
    
    if missing:
        print_warning(f"Missing dependencies: {', '.join(missing)}")
        print_info("Install them using your package manager:")
        if platform.system() == "Linux":
            print(f"  sudo apt install {' '.join(missing)}")
        elif platform.system() == "Darwin":
            print(f"  brew install {' '.join(missing)}")
    
    return len(missing) == 0


def create_directories():
    """Create necessary directories"""
    directories = [
        "data",
        "logs",
        "config",
        "static",
        "static/js",
        "static/css",
        "static/img",
        "backups",
        "temp",
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True)
            print_success(f"Created directory: {directory}")
        else:
            print_info(f"Directory exists: {directory}")
    
    return True


def setup_virtual_environment():
    """Setup Python virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print_info("Virtual environment already exists")
        response = input("Recreate virtual environment? (y/N): ").lower()
        if response != 'y':
            return True
        shutil.rmtree(venv_path)
    
    print_info("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    print_success("Virtual environment created")
    
    # Get pip path
    if platform.system() == "Windows":
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    # Upgrade pip
    print_info("Upgrading pip...")
    subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], 
                   capture_output=True, check=True)
    
    # Install requirements
    if Path("requirements.txt").exists():
        print_info("Installing requirements...")
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], 
                       check=True)
        print_success("Requirements installed")
    else:
        print_warning("requirements.txt not found")
    
    return True


def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(32)


def generate_api_key():
    """Generate a secure API key"""
    return f"sm_{secrets.token_urlsafe(32)}"


def create_env_file():
    """Create .env configuration file"""
    env_path = Path(".env")
    
    if env_path.exists():
        print_warning(".env file already exists")
        response = input("Overwrite? (y/N): ").lower()
        if response != 'y':
            return True
        # Backup existing
        shutil.copy(".env", ".env.backup")
        print_info("Backed up existing .env to .env.backup")
    
    print_info("Creating .env file...")
    
    # Get configuration from user
    config = {}
    
    print("\n📝 Basic Configuration:")
    config['HOST'] = input(f"Host [0.0.0.0]: ") or "0.0.0.0"
    config['PORT'] = input(f"Port [8000]: ") or "8000"
    
    print("\n🔐 Security Configuration:")
    enable_api_key = input(f"Enable API key authentication? [y/n]: ").lower()
    config['API_KEY_ENABLED'] = "true" if enable_api_key == 'y' else "false"
    
    if enable_api_key == 'y':
        config['API_KEY'] = generate_api_key()
        print_success(f"Generated API key: {Colors.BOLD}{config['API_KEY']}{Colors.ENDC}")
        print_warning("Save this API key securely!")
    else:
        config['API_KEY'] = ""
    
    config['SECRET_KEY'] = generate_secret_key()
    
    # Write .env file
    env_content = f"""# Sync Manager Configuration
# Generated by install.py

# Server Configuration
HOST={config['HOST']}
PORT={config['PORT']}
WORKERS=4
DEBUG=false

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/sync_manager.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/sync_manager.log

# Security
SECRET_KEY={config['SECRET_KEY']}
API_KEY_ENABLED={config['API_KEY_ENABLED']}
API_KEY={config['API_KEY']}

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
"""

    with open(".env", "w") as f:
        f.write(env_content)
    
    print_success(".env file created")
    return True


def print_next_steps():
    """Print next steps after installation"""
    print_header("INSTALLATION COMPLETE")
    
    print(f"\n{Colors.OKGREEN}✨ Sync Manager has been successfully installed!{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Next steps:{Colors.ENDC}")
    print("1. Activate virtual environment:")
    if platform.system() == "Windows":
        print("   .\\venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("\n2. Start the server:")
    print("   python main.py")
    
    print("\n3. Access the API:")
    print("   http://localhost:8000/docs")
    
    print(f"\n{Colors.BOLD}Happy syncing! 🚀{Colors.ENDC}\n")


def main():
    """Main installation function"""
    print_header("SYNC MANAGER INSTALLATION")
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Checking system", check_system),
        ("Checking dependencies", check_dependencies),
        ("Creating directories", create_directories),
        ("Setting up virtual environment", setup_virtual_environment),
        ("Creating configuration file", create_env_file),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{Colors.BOLD}📦 {step_name}...{Colors.ENDC}")
        if not step_func():
            print_error(f"Installation failed at: {step_name}")
            sys.exit(1)
    
    print_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Installation failed: {e}")
        sys.exit(1)
