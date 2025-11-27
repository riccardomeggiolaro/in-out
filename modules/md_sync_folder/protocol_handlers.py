"""
Protocol handlers for remote file synchronization
Supports Samba/CIFS, FTP, and SFTP protocols
"""

from abc import ABC, abstractmethod
import os
import shutil
import subprocess
from ftplib import FTP, FTP_TLS
import paramiko
from typing import Tuple, Optional
import libs.lb_log as lb_log
import libs.lb_system as lb_system
from modules.md_sync_folder.dto import SyncFolderDTO


class ProtocolHandler(ABC):
    """Abstract base class for protocol handlers"""

    def __init__(self, config: SyncFolderDTO):
        self.config = config
        self.connected = False

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to remote server"""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Close connection to remote server"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active"""
        pass

    @abstractmethod
    def copy_file(self, local_path: str, remote_path: str) -> bool:
        """Copy a file to remote server"""
        pass

    @abstractmethod
    def copy_directory(self, local_path: str, remote_path: str) -> bool:
        """Copy a directory to remote server"""
        pass

    @abstractmethod
    def get_connection_status(self) -> Tuple[bool, Optional[str], str]:
        """Get connection status information"""
        pass


class SambaProtocolHandler(ProtocolHandler):
    """Handler for Samba/CIFS protocol using OS-level mounting"""

    def __init__(self, config: SyncFolderDTO, local_dir: str, mount_point: str):
        super().__init__(config)
        self.local_dir = local_dir
        self.mount_point = mount_point

    def connect(self) -> bool:
        """Mount Samba share"""
        return lb_system.mount_remote(
            self.config.ip,
            self.config.domain,
            self.config.share_name,
            self.config.username,
            self.config.password,
            self.local_dir,
            self.mount_point
        )

    def disconnect(self) -> bool:
        """Unmount Samba share"""
        return lb_system.umount_remote(self.mount_point)

    def is_connected(self) -> bool:
        """Check if Samba share is mounted"""
        return lb_system.is_mounted(self.mount_point)

    def copy_file(self, local_path: str, remote_path: str) -> bool:
        """Copy file using shutil (mounted filesystem)"""
        try:
            os.makedirs(os.path.dirname(remote_path), exist_ok=True)
            shutil.copy(local_path, remote_path)
            return True
        except Exception as e:
            lb_log.error(f"Samba copy_file error: {e}")
            return False

    def copy_directory(self, local_path: str, remote_path: str) -> bool:
        """Copy directory using shutil (mounted filesystem)"""
        try:
            shutil.copytree(local_path, remote_path, dirs_exist_ok=True)
            return True
        except Exception as e:
            lb_log.error(f"Samba copy_directory error: {e}")
            return False

    def get_connection_status(self) -> Tuple[bool, Optional[str], str]:
        """Get Samba mount status"""
        return lb_system.get_remote_connection_status(self.mount_point)

    def get_remote_path(self, local_path: str, local_dir: str, sub_path: str) -> str:
        """Calculate remote path for Samba (uses mount point)"""
        rel_path = os.path.relpath(local_path, local_dir)

        # Normalize paths for comparison
        norm_sub_path = os.path.normpath(sub_path).replace('\\', '/')
        norm_rel_path = os.path.normpath(rel_path).replace('\\', '/')

        # Remove sub_path from rel_path if it exists to avoid duplication
        if norm_sub_path and norm_rel_path.startswith(norm_sub_path + '/'):
            rel_path = rel_path[len(sub_path) + 1:]
        elif norm_sub_path and norm_rel_path == norm_sub_path:
            rel_path = os.path.basename(local_path)

        remote_path = os.path.join(self.mount_point, sub_path, rel_path) if rel_path else os.path.join(self.mount_point, sub_path, os.path.basename(local_path))
        return os.path.normpath(remote_path)


class FTPProtocolHandler(ProtocolHandler):
    """Handler for FTP protocol"""

    def __init__(self, config: SyncFolderDTO):
        super().__init__(config)
        self.ftp = None
        self.use_tls = False

    def connect(self) -> bool:
        """Connect to FTP server"""
        try:
            if self.ftp:
                try:
                    self.ftp.quit()
                except:
                    pass

            # Try FTP_TLS first for security, fallback to regular FTP
            try:
                self.ftp = FTP_TLS()
                self.ftp.connect(self.config.ip, self.config.port or 21, timeout=10)
                self.ftp.login(self.config.username, self.config.password)
                self.ftp.prot_p()  # Enable secure data connection
                self.use_tls = True
                lb_log.info("Connected using FTPS (FTP with TLS)")
            except:
                # Fallback to regular FTP
                self.ftp = FTP()
                self.ftp.connect(self.config.ip, self.config.port or 21, timeout=10)
                self.ftp.login(self.config.username, self.config.password)
                self.use_tls = False
                lb_log.info("Connected using regular FTP")

            # Change to share_name directory if specified
            if self.config.share_name:
                try:
                    self.ftp.cwd(self.config.share_name)
                except:
                    # Try to create the directory if it doesn't exist
                    try:
                        self.ftp.mkd(self.config.share_name)
                        self.ftp.cwd(self.config.share_name)
                    except Exception as e:
                        lb_log.error(f"Cannot change to directory {self.config.share_name}: {e}")

            self.connected = True
            return True
        except Exception as e:
            lb_log.error(f"FTP connection error: {e}")
            self.connected = False
            return False

    def disconnect(self) -> bool:
        """Disconnect from FTP server"""
        try:
            if self.ftp:
                self.ftp.quit()
                self.ftp = None
            self.connected = False
            return True
        except Exception as e:
            lb_log.error(f"FTP disconnect error: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if FTP connection is active"""
        if not self.ftp or not self.connected:
            return False
        try:
            self.ftp.voidcmd("NOOP")
            return True
        except:
            self.connected = False
            return False

    def _ensure_remote_dir(self, remote_dir: str) -> bool:
        """Create remote directory structure if it doesn't exist"""
        try:
            dirs = remote_dir.replace('\\', '/').split('/')
            current_path = ""

            for dir_name in dirs:
                if not dir_name:
                    continue
                current_path += ('/' if current_path else '') + dir_name
                try:
                    self.ftp.cwd(current_path)
                except:
                    try:
                        self.ftp.mkd(current_path)
                        self.ftp.cwd(current_path)
                    except Exception as e:
                        lb_log.error(f"Cannot create directory {current_path}: {e}")
                        return False

            # Return to base directory (share_name)
            if self.config.share_name:
                self.ftp.cwd(f"/{self.config.share_name}")
            else:
                self.ftp.cwd("/")

            return True
        except Exception as e:
            lb_log.error(f"Error ensuring remote directory {remote_dir}: {e}")
            return False

    def copy_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file via FTP"""
        try:
            if not self.is_connected():
                if not self.connect():
                    return False

            # Ensure remote directory exists
            remote_dir = os.path.dirname(remote_path).replace('\\', '/')
            if remote_dir and not self._ensure_remote_dir(remote_dir):
                return False

            # Upload file
            with open(local_path, 'rb') as f:
                remote_file = remote_path.replace('\\', '/')
                self.ftp.storbinary(f'STOR {remote_file}', f)

            lb_log.info(f"FTP uploaded: {local_path} -> {remote_path}")
            return True
        except Exception as e:
            lb_log.error(f"FTP copy_file error: {e}")
            return False

    def copy_directory(self, local_path: str, remote_path: str) -> bool:
        """Upload directory recursively via FTP"""
        try:
            if not self.is_connected():
                if not self.connect():
                    return False

            # Create remote directory
            remote_path = remote_path.replace('\\', '/')
            if not self._ensure_remote_dir(remote_path):
                return False

            # Upload all files in directory
            for root, dirs, files in os.walk(local_path):
                rel_root = os.path.relpath(root, local_path)
                if rel_root == '.':
                    remote_root = remote_path
                else:
                    remote_root = os.path.join(remote_path, rel_root).replace('\\', '/')

                # Create subdirectories
                for dir_name in dirs:
                    remote_subdir = os.path.join(remote_root, dir_name).replace('\\', '/')
                    self._ensure_remote_dir(remote_subdir)

                # Upload files
                for file_name in files:
                    local_file = os.path.join(root, file_name)
                    remote_file = os.path.join(remote_root, file_name).replace('\\', '/')
                    if not self.copy_file(local_file, remote_file):
                        return False

            lb_log.info(f"FTP uploaded directory: {local_path} -> {remote_path}")
            return True
        except Exception as e:
            lb_log.error(f"FTP copy_directory error: {e}")
            return False

    def get_connection_status(self) -> Tuple[bool, Optional[str], str]:
        """Get FTP connection status"""
        if self.is_connected():
            remote_path = f"ftp://{self.config.ip}:{self.config.port or 21}/{self.config.share_name}"
            status = f"connected ({'FTPS' if self.use_tls else 'FTP'})"
            return True, remote_path, status
        else:
            return False, None, "disconnected"

    def get_remote_path(self, local_path: str, local_dir: str, sub_path: str) -> str:
        """Calculate remote path for FTP"""
        rel_path = os.path.relpath(local_path, local_dir)

        # Normalize paths
        norm_sub_path = os.path.normpath(sub_path).replace('\\', '/')
        norm_rel_path = os.path.normpath(rel_path).replace('\\', '/')

        # Remove sub_path from rel_path if it exists
        if norm_sub_path and norm_rel_path.startswith(norm_sub_path + '/'):
            rel_path = rel_path[len(sub_path) + 1:]
        elif norm_sub_path and norm_rel_path == norm_sub_path:
            rel_path = os.path.basename(local_path)

        remote_path = os.path.join(sub_path, rel_path).replace('\\', '/') if rel_path else os.path.join(sub_path, os.path.basename(local_path)).replace('\\', '/')
        return remote_path


class SFTPProtocolHandler(ProtocolHandler):
    """Handler for SFTP protocol"""

    def __init__(self, config: SyncFolderDTO):
        super().__init__(config)
        self.ssh = None
        self.sftp = None

    def connect(self) -> bool:
        """Connect to SFTP server"""
        try:
            if self.ssh:
                try:
                    self.ssh.close()
                except:
                    pass

            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                self.config.ip,
                port=self.config.port or 22,
                username=self.config.username,
                password=self.config.password,
                timeout=10
            )

            self.sftp = self.ssh.open_sftp()

            # Change to share_name directory if specified
            if self.config.share_name:
                try:
                    self.sftp.chdir(self.config.share_name)
                except:
                    # Try to create the directory if it doesn't exist
                    try:
                        self.sftp.mkdir(self.config.share_name)
                        self.sftp.chdir(self.config.share_name)
                    except Exception as e:
                        lb_log.error(f"Cannot change to directory {self.config.share_name}: {e}")

            self.connected = True
            lb_log.info(f"SFTP connected to {self.config.ip}:{self.config.port or 22}")
            return True
        except Exception as e:
            lb_log.error(f"SFTP connection error: {e}")
            self.connected = False
            return False

    def disconnect(self) -> bool:
        """Disconnect from SFTP server"""
        try:
            if self.sftp:
                self.sftp.close()
                self.sftp = None
            if self.ssh:
                self.ssh.close()
                self.ssh = None
            self.connected = False
            return True
        except Exception as e:
            lb_log.error(f"SFTP disconnect error: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if SFTP connection is active"""
        if not self.ssh or not self.sftp or not self.connected:
            return False
        try:
            self.sftp.listdir('.')
            return True
        except:
            self.connected = False
            return False

    def _ensure_remote_dir(self, remote_dir: str) -> bool:
        """Create remote directory structure if it doesn't exist"""
        try:
            dirs = remote_dir.replace('\\', '/').split('/')
            current_path = ""

            for dir_name in dirs:
                if not dir_name:
                    continue
                current_path += ('/' if current_path else '') + dir_name
                try:
                    self.sftp.stat(current_path)
                except:
                    try:
                        self.sftp.mkdir(current_path)
                    except Exception as e:
                        lb_log.error(f"Cannot create directory {current_path}: {e}")
                        return False

            return True
        except Exception as e:
            lb_log.error(f"Error ensuring remote directory {remote_dir}: {e}")
            return False

    def copy_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file via SFTP"""
        try:
            if not self.is_connected():
                if not self.connect():
                    return False

            # Ensure remote directory exists
            remote_dir = os.path.dirname(remote_path).replace('\\', '/')
            if remote_dir and not self._ensure_remote_dir(remote_dir):
                return False

            # Upload file
            remote_file = remote_path.replace('\\', '/')
            self.sftp.put(local_path, remote_file)

            lb_log.info(f"SFTP uploaded: {local_path} -> {remote_path}")
            return True
        except Exception as e:
            lb_log.error(f"SFTP copy_file error: {e}")
            return False

    def copy_directory(self, local_path: str, remote_path: str) -> bool:
        """Upload directory recursively via SFTP"""
        try:
            if not self.is_connected():
                if not self.connect():
                    return False

            # Create remote directory
            remote_path = remote_path.replace('\\', '/')
            if not self._ensure_remote_dir(remote_path):
                return False

            # Upload all files in directory
            for root, dirs, files in os.walk(local_path):
                rel_root = os.path.relpath(root, local_path)
                if rel_root == '.':
                    remote_root = remote_path
                else:
                    remote_root = os.path.join(remote_path, rel_root).replace('\\', '/')

                # Create subdirectories
                for dir_name in dirs:
                    remote_subdir = os.path.join(remote_root, dir_name).replace('\\', '/')
                    self._ensure_remote_dir(remote_subdir)

                # Upload files
                for file_name in files:
                    local_file = os.path.join(root, file_name)
                    remote_file = os.path.join(remote_root, file_name).replace('\\', '/')
                    if not self.copy_file(local_file, remote_file):
                        return False

            lb_log.info(f"SFTP uploaded directory: {local_path} -> {remote_path}")
            return True
        except Exception as e:
            lb_log.error(f"SFTP copy_directory error: {e}")
            return False

    def get_connection_status(self) -> Tuple[bool, Optional[str], str]:
        """Get SFTP connection status"""
        if self.is_connected():
            remote_path = f"sftp://{self.config.ip}:{self.config.port or 22}/{self.config.share_name}"
            return True, remote_path, "connected"
        else:
            return False, None, "disconnected"

    def get_remote_path(self, local_path: str, local_dir: str, sub_path: str) -> str:
        """Calculate remote path for SFTP"""
        rel_path = os.path.relpath(local_path, local_dir)

        # Normalize paths
        norm_sub_path = os.path.normpath(sub_path).replace('\\', '/')
        norm_rel_path = os.path.normpath(rel_path).replace('\\', '/')

        # Remove sub_path from rel_path if it exists
        if norm_sub_path and norm_rel_path.startswith(norm_sub_path + '/'):
            rel_path = rel_path[len(sub_path) + 1:]
        elif norm_sub_path and norm_rel_path == norm_sub_path:
            rel_path = os.path.basename(local_path)

        remote_path = os.path.join(sub_path, rel_path).replace('\\', '/') if rel_path else os.path.join(sub_path, os.path.basename(local_path)).replace('\\', '/')
        return remote_path


def create_protocol_handler(config: SyncFolderDTO, local_dir: str = None, mount_point: str = None) -> ProtocolHandler:
    """Factory function to create appropriate protocol handler"""
    protocol = config.protocol.lower()

    if protocol == "samba":
        if not local_dir or not mount_point:
            raise ValueError("local_dir and mount_point required for Samba protocol")
        return SambaProtocolHandler(config, local_dir, mount_point)
    elif protocol == "ftp":
        return FTPProtocolHandler(config)
    elif protocol == "sftp":
        return SFTPProtocolHandler(config)
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")
