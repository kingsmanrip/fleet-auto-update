#!/usr/bin/env python3
import os
import sys
import requests
import logging
import time
from packaging import version
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pi2/fleet_client/version_checker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
VERSION_URL = "https://www.dropbox.com/scl/fi/7g0um2w6dkjvv7kzcjw4d/appNewVersion.txt?rlkey=d2zbrulifx6bsja9xv4v6l1wo&st=3fz3jqd9&dl=1"
CODE_URL = "https://www.dropbox.com/scl/fi/9kon3isw564jxh7uewnr9/send.txt?rlkey=dy6kmnjzdt1o6fjjhs9xl7rdy&st=jmrcybda&dl=1"
VERSION_FILE = "/home/pi2/fleet_client/current_version.txt"
SCRIPT_PATH = "/home/pi2/fleet_client/send.py"
BACKUP_PATH = "/home/pi2/fleet_client/send.py.backup"

def get_current_version():
    """Read the current version from the version file"""
    try:
        if not os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'w') as f:
                f.write('1.0.0')
            return '1.0.0'
        
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"Error reading current version: {e}")
        return '1.0.0'

def get_remote_version():
    """Fetch the latest version number from Dropbox"""
    try:
        response = requests.get(VERSION_URL)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error fetching remote version: {e}")
        return None

def backup_current_script():
    """Create a backup of the current script"""
    try:
        if os.path.exists(SCRIPT_PATH):
            os.replace(SCRIPT_PATH, BACKUP_PATH)
            logger.info("Created backup of current script")
            return True
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
    return False

def restore_backup():
    """Restore the script from backup if update fails"""
    try:
        if os.path.exists(BACKUP_PATH):
            os.replace(BACKUP_PATH, SCRIPT_PATH)
            logger.info("Restored script from backup")
            return True
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
    return False

def update_script():
    """Download and update the script"""
    try:
        response = requests.get(CODE_URL)
        response.raise_for_status()
        
        # Create backup first
        if not backup_current_script():
            raise Exception("Failed to create backup")
        
        # Write new content
        with open(SCRIPT_PATH, 'wb') as f:
            f.write(response.content)
        
        # Set execute permissions
        os.chmod(SCRIPT_PATH, 0o755)
        
        logger.info("Successfully updated script")
        return True
    except Exception as e:
        logger.error(f"Error updating script: {e}")
        if not restore_backup():
            logger.error("Failed to restore backup!")
        return False

def update_version_file(new_version):
    """Update the version file with new version"""
    try:
        with open(VERSION_FILE, 'w') as f:
            f.write(new_version)
        logger.info(f"Updated version file to {new_version}")
        return True
    except Exception as e:
        logger.error(f"Error updating version file: {e}")
        return False

def check_and_update():
    """Main function to check and perform updates"""
    logger.info("Starting version check")
    
    current_version = get_current_version()
    logger.info(f"Current version: {current_version}")
    
    remote_version = get_remote_version()
    if not remote_version:
        logger.error("Failed to get remote version")
        return
    
    logger.info(f"Remote version: {remote_version}")
    
    try:
        if version.parse(remote_version) > version.parse(current_version):
            logger.info("New version available, updating...")
            if update_script() and update_version_file(remote_version):
                logger.info("Update completed successfully")
            else:
                logger.error("Update failed")
        else:
            logger.info("Already running latest version")
    except Exception as e:
        logger.error(f"Error comparing versions: {e}")

def main():
    """Main execution loop"""
    while True:
        try:
            check_and_update()
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        
        # Wait for 5 minutes before next check
        time.sleep(300)

if __name__ == "__main__":
    main()
