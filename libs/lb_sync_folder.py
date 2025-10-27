# Function to mount the remote share
def mount_remote(config):
    if not config:
        return False
    ip = config['ip']
    share_name = config['share_name']  # Use share_name for mounting
    user = config['username']
    pwd = config['password']
    if system == 'Linux':
        if os.path.ismount(mount_point):
            logger.info(f"Unmounting existing mount at {mount_point}")
            try:
                subprocess.check_call(['umount', mount_point])
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to unmount {mount_point}: {e}")
                return False
        cmd = [
            'mount', '-t', 'cifs', f'//{ip}/{share_name}', mount_point,
            '-o', f'username={user},password={pwd}'
        ]
    elif system == 'Windows':
        cmd = [
            'net', 'use', mount_point, f'\\\\{ip}\\{share_name}',
            f'/user:{user}', pwd
        ]
        # For Windows, check if mounted and unmount
        try:
            subprocess.check_call(['net', 'use', mount_point])
            logger.info(f"Unmounting existing mount at {mount_point}")
            subprocess.check_call(['net', 'use', mount_point, '/delete'])
        except subprocess.CalledProcessError:
            pass  # Not mounted, proceed
    try:
        subprocess.check_call(cmd)
        logger.info(f"Mounted remote share {share_name} at {mount_point}")
        # Verify mount is not empty
        if not os.listdir(mount_point):
            logger.warning(f"Mount point {mount_point} is empty")
            return False
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to mount remote share {share_name}: {e}")
        return False
    except OSError as e:
        logger.error(f"Error accessing mount point {mount_point}: {e}")
        return False