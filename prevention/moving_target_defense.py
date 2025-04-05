import os
import random
import time
import hashlib
import shutil
import logging
from pathlib import Path
from utils.file_hopper import get_file_hopper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/prevention.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MovingTargetDefense")

def rotate_file_paths():
    """
    Implement Moving Target Defense by rotating file paths.
    Returns tuple of (success, list of moved files)
    """
    try:
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Get file hopper instance
        file_hopper = get_file_hopper()
        
        # Initialize the MTD rotation
        suspicious_files = []
        for root, _, files in os.walk('test_data'):
            for file in files:
                # Check if file has suspicious extension
                if any(file.endswith(ext) for ext in ['.locked', '.encrypted', '.crypto', '.crypt']):
                    file_path = os.path.join(root, file)
                    suspicious_files.append(file_path)
        
        if not suspicious_files:
            logger.info("No suspicious files found to rotate")
            return True, []
        
        # Ensure MTD directory exists
        os.makedirs('safe_mtd', exist_ok=True)
        
        # Track successful moves
        moved_files = []
        
        # Process suspicious files
        for source in suspicious_files:
            try:
                # Get a random hop location
                hop_locations = file_hopper.get_available_locations()
                
                if not hop_locations:
                    logger.error("No hop locations available")
                    continue
                
                # Choose a random location
                hop_dir_name = random.choice(hop_locations)
                hop_dir = os.path.join('safe_mtd', hop_dir_name)
                
                # Create a unique filename for security
                original_filename = os.path.basename(source)
                file_hash = hashlib.md5(f"{original_filename}-{time.time()}".encode()).hexdigest()[:8]
                secure_filename = f"{file_hash}_{original_filename}"
                
                # Create destination path
                destination = os.path.join(hop_dir, secure_filename)
                
                # Move the file
                shutil.copy2(source, destination)  # Copy first to avoid data loss
                
                # Log the movement
                logger.info(f"Moved suspicious file: {source} -> {destination}")
                moved_files.append((source, destination))
                
                # Add to MTD routes log
                os.makedirs('prevention', exist_ok=True)
                with open('prevention/mtd_routes.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{source} → {destination}\n")
                    
                # After successful copy, remove original if it exists
                if os.path.exists(source):
                    os.remove(source)
                
            except Exception as e:
                logger.error(f"Error moving file {source}: {e}")
        
        # Start the file hopper if files were moved
        if moved_files:
            file_hopper.start()
            
        return True, moved_files
            
    except Exception as e:
        logger.error(f"Error in rotate_file_paths: {e}")
        return False, []

def check_mtd_status():
    """Check the status of MTD operations"""
    try:
        # Get file hopper instance
        file_hopper = get_file_hopper()
        
        # Get current file locations
        current_files = file_hopper.get_file_locations()
        
        # Get hop history
        hop_history = file_hopper.get_hop_history()
        
        # Return status information
        return {
            'active': file_hopper.running,
            'protected_files': len(current_files),
            'hop_count': len(hop_history),
            'last_hop': hop_history[-1]['timestamp'] if hop_history else None
        }
    except Exception as e:
        logger.error(f"Error checking MTD status: {e}")
        return {
            'active': False,
            'protected_files': 0,
            'hop_count': 0,
            'last_hop': None,
            'error': str(e)
        }

def stop_mtd():
    """Stop Moving Target Defense operations"""
    try:
        # Get file hopper instance
        file_hopper = get_file_hopper()
        
        # Stop the file hopper
        result = file_hopper.stop()
        
        return result
    except Exception as e:
        logger.error(f"Error stopping MTD: {e}")
        return False

def restore_files(destination_dir=None):
    """
    Restore all protected files to a destination directory.
    If destination_dir is None, restore to 'restored_files' directory.
    
    Returns tuple of (success, restored_files)
    """
    try:
        # Get file hopper instance
        file_hopper = get_file_hopper()
        
        # Stop file hopping during restoration
        file_hopper.stop()
        
        # Set up destination directory
        if destination_dir is None:
            destination_dir = 'restored_files'
        
        os.makedirs(destination_dir, exist_ok=True)
        
        # Get all current file locations
        current_files = file_hopper.get_file_locations()
        
        restored_files = []
        
        # Copy files to destination
        for file_info in current_files:
            try:
                source_path = file_info['path']
                filename = file_info['name']
                
                # Extract original filename if it has our hash prefix
                if '_' in filename and len(filename.split('_')[0]) == 8:
                    # Remove hash prefix
                    filename = '_'.join(filename.split('_')[1:])
                
                destination_path = os.path.join(destination_dir, filename)
                
                # Copy the file
                shutil.copy2(source_path, destination_path)
                
                restored_files.append((source_path, destination_path))
                logger.info(f"Restored file: {source_path} -> {destination_path}")
                
            except Exception as e:
                logger.error(f"Error restoring file {file_info['path']}: {e}")
        
        return True, restored_files
        
    except Exception as e:
        logger.error(f"Error in restore_files: {e}")
        return False, []

# For testing
if __name__ == "__main__":
    success, moved_files = rotate_file_paths()
    print(f"Success: {success}")
    print(f"Moved files: {moved_files}")
    
    # Wait a bit to see file hopping in action
    print("Waiting for file hopping...")
    time.sleep(10)
    
    # Check status
    status = check_mtd_status()
    print(f"MTD Status: {status}")
    
    # Stop MTD
    stop_result = stop_mtd()
    print(f"Stop result: {stop_result}")