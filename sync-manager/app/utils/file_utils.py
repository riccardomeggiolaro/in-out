"""
Utility functions for Sync Manager
"""

import hashlib
import os
import re
from pathlib import Path
from typing import List, Optional
import fnmatch


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate hash of a file"""
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def get_file_size(file_path: str) -> float:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0


def is_file_match_patterns(
    file_path: str,
    include_patterns: List[str],
    exclude_patterns: List[str]
) -> bool:
    """Check if file matches include/exclude patterns"""
    file_name = os.path.basename(file_path)
    
    # If exclude patterns are specified and file matches any, exclude it
    if exclude_patterns:
        for pattern in exclude_patterns:
            if pattern.startswith("regex:"):
                # Regex pattern
                regex = re.compile(pattern[6:])
                if regex.match(file_name):
                    return False
            else:
                # Glob pattern
                if fnmatch.fnmatch(file_name, pattern):
                    return False
    
    # If include patterns are specified, file must match at least one
    if include_patterns:
        for pattern in include_patterns:
            if pattern.startswith("regex:"):
                # Regex pattern
                regex = re.compile(pattern[6:])
                if regex.match(file_name):
                    return True
            else:
                # Glob pattern
                if fnmatch.fnmatch(file_name, pattern):
                    return True
        return False  # Didn't match any include pattern
    
    # No include patterns specified, include by default
    return True


def format_bytes(bytes_value: float) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def sanitize_path(path: str) -> str:
    """Sanitize file path to prevent directory traversal"""
    # Remove any parent directory references
    path = os.path.normpath(path)
    path = path.replace("../", "").replace("..", "")
    
    # Remove leading slashes for relative paths
    if path.startswith("/") and not os.path.isabs(path):
        path = path.lstrip("/")
    
    return path


def ensure_directory(path: str) -> Path:
    """Ensure directory exists, create if not"""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def is_safe_path(path: str, base_path: str) -> bool:
    """Check if path is safe (within base path)"""
    try:
        # Resolve to absolute paths
        base = Path(base_path).resolve()
        target = Path(path).resolve()
        
        # Check if target is within base
        return target.parts[:len(base.parts)] == base.parts
    except:
        return False


def get_relative_path(file_path: str, base_path: str) -> str:
    """Get relative path from base path"""
    try:
        return str(Path(file_path).relative_to(base_path))
    except:
        return os.path.basename(file_path)


def parse_cron_expression(cron_expr: str) -> dict:
    """Parse cron expression to dict"""
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError("Invalid cron expression")
    
    return {
        "minute": parts[0],
        "hour": parts[1],
        "day": parts[2],
        "month": parts[3],
        "weekday": parts[4]
    }


def validate_network_path(path: str) -> bool:
    """Validate network path format"""
    # Check for SMB/CIFS paths
    if path.startswith("//") or path.startswith("\\\\"):
        return True
    
    # Check for NFS paths
    if ":" in path and not path[1] == ":":  # Not a Windows drive
        return True
    
    # Check for mounted network drives
    if os.path.exists(path) and os.path.ismount(path):
        return True
    
    return False


def get_mount_point(path: str) -> Optional[str]:
    """Get mount point of a path"""
    path = Path(path).resolve()
    
    while not os.path.ismount(path) and path.parent != path:
        path = path.parent
    
    if os.path.ismount(path):
        return str(path)
    
    return None


def check_disk_space(path: str, required_bytes: int) -> bool:
    """Check if enough disk space is available"""
    try:
        stat = os.statvfs(path)
        available_bytes = stat.f_bavail * stat.f_frsize
        return available_bytes >= required_bytes
    except:
        return True  # Assume enough space if can't check


def list_files_recursive(
    directory: str,
    include_patterns: List[str] = None,
    exclude_patterns: List[str] = None,
    max_depth: int = None
) -> List[str]:
    """List files recursively with pattern matching"""
    files = []
    base_depth = len(Path(directory).parts)
    
    for root, dirs, filenames in os.walk(directory):
        # Check depth
        if max_depth:
            current_depth = len(Path(root).parts) - base_depth
            if current_depth >= max_depth:
                dirs.clear()  # Don't go deeper
        
        # Process files
        for filename in filenames:
            file_path = os.path.join(root, filename)
            
            if is_file_match_patterns(file_path, include_patterns or [], exclude_patterns or []):
                files.append(file_path)
    
    return files


def atomic_write(file_path: str, content: bytes) -> bool:
    """Write file atomically using temporary file"""
    temp_path = f"{file_path}.tmp"
    
    try:
        # Write to temporary file
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Atomic rename
        os.replace(temp_path, file_path)
        return True
    except Exception as e:
        # Clean up temp file if exists
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def get_file_metadata(file_path: str) -> dict:
    """Get comprehensive file metadata"""
    try:
        stat = os.stat(file_path)
        path = Path(file_path)
        
        return {
            "path": file_path,
            "name": path.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "accessed": stat.st_atime,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "is_symlink": path.is_symlink(),
            "extension": path.suffix,
            "permissions": oct(stat.st_mode)[-3:],
        }
    except Exception as e:
        return {"error": str(e)}
