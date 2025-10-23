#!/usr/bin/env python3
"""
Migration Script - Migrate from Bash Sync System to Python Sync Manager

This script helps migrate existing bash-based sync configurations
to the new Python Sync Manager system.
"""

import os
import re
import json
import asyncio
import configparser
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import init_db, AsyncSessionLocal, DatabaseManager


class BashConfigParser:
    """Parse bash sync configurations"""
    
    def __init__(self):
        self.configs = []
    
    def parse_bash_script(self, script_path: str) -> Dict:
        """Parse a bash sync script to extract configuration"""
        config = {
            "name": Path(script_path).stem,
            "source_path": None,
            "destination_path": None,
            "delete_after_sync": True,
            "sync_interval": 5,
            "enabled": False,
            "exclude_patterns": [],
            "include_patterns": []
        }
        
        try:
            with open(script_path, 'r') as f:
                content = f.read()
                
                # Extract source path
                source_match = re.search(r'CARTELLA_LOCALE[=\s]+"?([^"\n]+)"?', content)
                if source_match:
                    config["source_path"] = source_match.group(1).replace('$HOME', str(Path.home()))
                
                # Extract destination path
                dest_match = re.search(r'CARTELLA_RETE[=\s]+"?([^"\n]+)"?', content)
                if dest_match:
                    config["destination_path"] = dest_match.group(1).replace('$HOME', str(Path.home()))
                
                # Extract sync interval
                interval_match = re.search(r'INTERVALLO_CONTROLLO[=\s]+(\d+)', content)
                if interval_match:
                    config["sync_interval"] = int(interval_match.group(1))
                
                # Extract max retries
                retry_match = re.search(r'MAX_RETRY[=\s]+(\d+)', content)
                if retry_match:
                    config["max_retries"] = int(retry_match.group(1))
                
                # Check for exclude patterns
                exclude_matches = re.findall(r'\*\.(tmp|lock|db|swp)', content)
                if exclude_matches:
                    config["exclude_patterns"] = [f"*.{ext}" for ext in exclude_matches]
                
                # Add common excludes
                if "node_modules" in content:
                    config["exclude_patterns"].append("node_modules")
                if "__pycache__" in content:
                    config["exclude_patterns"].append("__pycache__")
                
        except Exception as e:
            print(f"Error parsing {script_path}: {e}")
        
        return config
    
    def parse_env_file(self, env_path: str) -> Dict:
        """Parse environment file for configuration"""
        config = {}
        
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            
                            # Map to our config keys
                            if key == "CARTELLA_LOCALE":
                                config["source_path"] = value.replace('$HOME', str(Path.home()))
                            elif key == "CARTELLA_RETE":
                                config["destination_path"] = value.replace('$HOME', str(Path.home()))
                            elif key == "INTERVALLO_CONTROLLO":
                                config["sync_interval"] = int(value)
                            elif key == "MAX_RETRY":
                                config["max_retries"] = int(value)
        except Exception as e:
            print(f"Error parsing {env_path}: {e}")
        
        return config
    
    def parse_systemd_service(self, service_path: str) -> Optional[Dict]:
        """Parse systemd service file"""
        config = configparser.ConfigParser()
        
        try:
            config.read(service_path)
            
            if 'Service' in config:
                exec_start = config['Service'].get('ExecStart', '')
                
                # Extract script path and arguments
                parts = exec_start.split()
                if len(parts) >= 3:
                    return {
                        "name": Path(service_path).stem,
                        "source_path": parts[-2],
                        "destination_path": parts[-1],
                        "enabled": True
                    }
        except Exception as e:
            print(f"Error parsing {service_path}: {e}")
        
        return None
    
    def find_bash_configs(self) -> List[Dict]:
        """Find and parse all bash sync configurations"""
        configs = []
        
        # Common locations to check
        search_paths = [
            Path.home() / "sync-folder",
            Path.home() / ".local" / "bin",
            Path("/opt/sync-folder"),
            Path.cwd()
        ]
        
        for base_path in search_paths:
            if base_path.exists():
                # Look for sync scripts
                for script in base_path.glob("*sync*.sh"):
                    print(f"Found script: {script}")
                    config = self.parse_bash_script(script)
                    if config["source_path"] and config["destination_path"]:
                        configs.append(config)
                
                # Look for env files
                for env_file in base_path.glob("*.env"):
                    print(f"Found env file: {env_file}")
                    env_config = self.parse_env_file(env_file)
                    if env_config:
                        configs.append(env_config)
        
        # Check systemd services
        systemd_path = Path("/etc/systemd/system")
        if systemd_path.exists():
            for service in systemd_path.glob("*sync*.service"):
                print(f"Found service: {service}")
                service_config = self.parse_systemd_service(service)
                if service_config:
                    configs.append(service_config)
        
        # Check crontab
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'sync' in line.lower() and not line.startswith('#'):
                        print(f"Found cron job: {line}")
                        # Try to extract paths from cron job
                        parts = line.split()
                        if len(parts) >= 7:
                            script_path = parts[5]
                            if Path(script_path).exists():
                                config = self.parse_bash_script(script_path)
                                if config["source_path"]:
                                    configs.append(config)
        except:
            pass
        
        return configs


class MountPointChecker:
    """Check and map mount points"""
    
    @staticmethod
    def get_mount_points() -> Dict[str, str]:
        """Get current mount points"""
        mounts = {}
        
        try:
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        device = parts[0]
                        mount_point = parts[1]
                        
                        # Filter network mounts
                        if any(x in device for x in ['://', 'cifs', 'nfs', 'smb']):
                            mounts[mount_point] = device
        except:
            pass
        
        return mounts
    
    @staticmethod
    def check_path_availability(path: str) -> bool:
        """Check if path is available"""
        path_obj = Path(path)
        
        if path_obj.exists():
            try:
                # Try to write test file
                test_file = path_obj / ".test_sync_migration"
                test_file.touch()
                test_file.unlink()
                return True
            except:
                pass
        
        return False


async def migrate_to_python(configs: List[Dict]):
    """Migrate configurations to Python Sync Manager"""
    
    # Initialize database
    await init_db()
    
    migrated = []
    failed = []
    
    async with AsyncSessionLocal() as session:
        for config in configs:
            try:
                # Validate paths
                if not config.get("source_path") or not config.get("destination_path"):
                    print(f"⚠️  Skipping config with missing paths: {config.get('name', 'Unknown')}")
                    failed.append(config)
                    continue
                
                # Check source path exists
                source_path = Path(config["source_path"])
                if not source_path.exists():
                    print(f"⚠️  Source path doesn't exist: {config['source_path']}")
                    response = input("Create it? (y/n): ").lower()
                    if response == 'y':
                        source_path.mkdir(parents=True, exist_ok=True)
                    else:
                        failed.append(config)
                        continue
                
                # Set default name if missing
                if not config.get("name"):
                    config["name"] = f"Migrated_{source_path.name}_to_{Path(config['destination_path']).name}"
                
                # Set default description
                if not config.get("description"):
                    config["description"] = f"Migrated from bash: {config['source_path']} -> {config['destination_path']}"
                
                # Create sync configuration
                print(f"Creating sync: {config['name']}")
                sync_config = await DatabaseManager.create_sync_config(session, config)
                
                migrated.append({
                    "id": sync_config.id,
                    "name": sync_config.name,
                    "source": sync_config.source_path,
                    "destination": sync_config.destination_path
                })
                
                print(f"✅ Migrated: {config['name']}")
                
            except Exception as e:
                print(f"❌ Failed to migrate {config.get('name', 'Unknown')}: {e}")
                failed.append(config)
    
    return migrated, failed


def print_migration_summary(migrated: List, failed: List, original_configs: List):
    """Print migration summary"""
    
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    
    print(f"\nTotal configurations found: {len(original_configs)}")
    print(f"Successfully migrated: {len(migrated)}")
    print(f"Failed to migrate: {len(failed)}")
    
    if migrated:
        print("\n✅ Successfully migrated:")
        for config in migrated:
            print(f"  - {config['name']} (ID: {config['id']})")
            print(f"    {config['source']} -> {config['destination']}")
    
    if failed:
        print("\n❌ Failed to migrate:")
        for config in failed:
            print(f"  - {config.get('name', 'Unknown')}")
            if config.get('source_path'):
                print(f"    Source: {config['source_path']}")
            if config.get('destination_path'):
                print(f"    Destination: {config['destination_path']}")
    
    print("\n" + "=" * 60)


def disable_old_services():
    """Disable old bash sync services"""
    
    print("\n🔧 Checking for old services to disable...")
    
    services_to_disable = []
    
    # Check systemd services
    try:
        result = subprocess.run(['systemctl', 'list-units', '--all'], 
                              capture_output=True, text=True)
        
        for line in result.stdout.split('\n'):
            if 'sync' in line.lower() and 'folder' in line.lower():
                parts = line.split()
                if parts:
                    service_name = parts[0]
                    if service_name.endswith('.service'):
                        services_to_disable.append(service_name)
    except:
        pass
    
    if services_to_disable:
        print(f"Found {len(services_to_disable)} old services:")
        for service in services_to_disable:
            print(f"  - {service}")
        
        response = input("\nDisable old services? (y/n): ").lower()
        if response == 'y':
            for service in services_to_disable:
                try:
                    subprocess.run(['sudo', 'systemctl', 'stop', service], check=True)
                    subprocess.run(['sudo', 'systemctl', 'disable', service], check=True)
                    print(f"  ✅ Disabled: {service}")
                except:
                    print(f"  ❌ Failed to disable: {service}")
    
    # Check crontab
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0 and 'sync' in result.stdout.lower():
            print("\n⚠️  Found sync jobs in crontab")
            print("Please manually review and remove old sync jobs:")
            print("  crontab -e")
    except:
        pass


async def main():
    """Main migration function"""
    
    print("=" * 60)
    print("BASH TO PYTHON SYNC MANAGER MIGRATION")
    print("=" * 60)
    
    # Parse existing configurations
    parser = BashConfigParser()
    print("\n🔍 Searching for existing bash configurations...")
    configs = parser.find_bash_configs()
    
    if not configs:
        print("\n❌ No bash sync configurations found")
        print("\nYou can manually add configurations using:")
        print("  - The web dashboard: http://localhost:8000")
        print("  - The API: http://localhost:8000/docs")
        print("  - The example client: python examples/client_example.py")
        return
    
    print(f"\n✅ Found {len(configs)} configuration(s)")
    
    # Display found configurations
    print("\nConfigurations to migrate:")
    for i, config in enumerate(configs, 1):
        print(f"\n{i}. {config.get('name', 'Unnamed')}")
        print(f"   Source: {config.get('source_path', 'N/A')}")
        print(f"   Destination: {config.get('destination_path', 'N/A')}")
        print(f"   Interval: {config.get('sync_interval', 5)}s")
        print(f"   Delete after sync: {config.get('delete_after_sync', True)}")
    
    # Check mount points
    print("\n🔍 Checking mount points...")
    mounts = MountPointChecker.get_mount_points()
    if mounts:
        print("Found network mounts:")
        for mount_point, device in mounts.items():
            print(f"  - {mount_point} -> {device}")
    
    # Confirm migration
    response = input("\n📦 Proceed with migration? (y/n): ").lower()
    if response != 'y':
        print("Migration cancelled")
        return
    
    # Perform migration
    print("\n🚀 Starting migration...")
    migrated, failed = await migrate_to_python(configs)
    
    # Print summary
    print_migration_summary(migrated, failed, configs)
    
    # Disable old services
    if migrated:
        disable_old_services()
    
    # Final instructions
    if migrated:
        print("\n✨ Migration complete!")
        print("\nNext steps:")
        print("1. Start the Python Sync Manager:")
        print("   python main.py")
        print("\n2. Access the dashboard:")
        print("   http://localhost:8000")
        print("\n3. Verify your migrated configurations:")
        print("   http://localhost:8000/docs")
        print("\n4. Start the migrated syncs:")
        print("   python examples/client_example.py")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
