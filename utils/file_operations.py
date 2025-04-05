import os
import shutil
import time
import random
import glob

def rotate_file_paths():
    try:
        # Define directories
        source_dirs = ["test_data", "suspicious_mtd"]
        destination_dir = "safe_mtd"
        
        # Create destination directory if it doesn't exist
        os.makedirs(destination_dir, exist_ok=True)
        
        # Create suspicious_mtd directory if it doesn't exist
        os.makedirs("suspicious_mtd", exist_ok=True)
        
        # Reset or verify log files
        os.makedirs('prevention', exist_ok=True)
        log_files = ['prevention/mtd_routes.txt', 'prevention/suspicious_transfers.txt', 'prevention/quarantine_log.txt']
        for log_file in log_files:
            if not os.path.exists(log_file):
                with open(log_file, 'w', encoding='utf-8') as f:
                    pass  # Create empty file

        # Track moved files with validation
        moved_files = []
        suspicious_mtd_transfers = []
        
        # Check for suspicious extensions
        suspicious_extensions = ['.locked', '.encrypted', '.crypto', '.crypt', '.crypted', 
                              '.crypz', '.encrypt', '.enc', '.ezz', '.exx', '.wncry', 
                              '.locky', '.kraken', '.cerber', '.zzz']
        
        # Track only actual file movements
        actual_moves = []
        
        # First, scan test_data for suspicious files
        if os.path.exists("test_data"):
            for extension in suspicious_extensions:
                suspicious_files = glob.glob(f"test_data/**/*{extension}", recursive=True)
                
                for file_path in suspicious_files:
                    if os.path.exists(file_path) and os.path.isfile(file_path):  # Validate file exists
                        filename = os.path.basename(file_path)
                        suspicious_path = os.path.join("suspicious_mtd", filename)
                        
                        try:
                            shutil.move(file_path, suspicious_path)
                            # Only count this as one move since it's the same file
                            actual_moves.append((file_path, suspicious_path))
                            
                            # Log suspicious transfer
                            with open('prevention/suspicious_transfers.txt', 'a', encoding='utf-8') as f:
                                f.write(f"{file_path} -> {suspicious_path}\n")
                                
                        except FileNotFoundError:
                            continue  # Skip if file disappeared
        
        # Now process suspicious_mtd files with validation
        if os.path.exists("suspicious_mtd"):
            files = [f for f in os.listdir("suspicious_mtd") 
                    if os.path.isfile(os.path.join("suspicious_mtd", f))]
            
            for file in files:
                source_path = os.path.join("suspicious_mtd", file)
                if os.path.exists(source_path):  # Validate file still exists
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    random_suffix = ''.join(random.choices('0123456789', k=4))
                    new_filename = f"quarantined_{timestamp}_{file}"  # Changed filename format
                    destination_path = os.path.join(destination_dir, new_filename)
                    
                    try:
                        shutil.move(source_path, destination_path)
                        # This is part of the same file movement, not a new file
                        actual_moves.append((source_path, destination_path))
                        
                        # Log MTD movement and quarantine entry
                        with open('prevention/mtd_routes.txt', 'a', encoding='utf-8') as f:
                            f.write(f"{source_path} -> {destination_path}\n")
                        
                        with open('prevention/quarantine_log.txt', 'a', encoding='utf-8') as f:
                            f.write(f"{source_path} -> {destination_path} @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                            
                    except FileNotFoundError:
                        continue  # Skip if file disappeared

        # Return unique file count
        unique_files = len(set(os.path.basename(src).split('_')[0] for src, _ in actual_moves))
        return unique_files > 0, actual_moves
        
    except Exception as e:
        print(f"Error in rotate_file_paths: {e}")
        return False, []

def scan_directory(directory_path):
    """Scan a directory for files and detect suspicious ones"""
    try:
        results = []
        suspicious_extensions = ['.locked', '.encrypted', '.crypto', '.crypt', '.crypted', 
                              '.crypz', '.encrypt', '.enc', '.ezz', '.exx', '.wncry', 
                              '.locky', '.kraken', '.cerber', '.zzz']
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_info = {'path': file_path}
                
                # Check if the file has suspicious extension
                if any(file.lower().endswith(ext) for ext in suspicious_extensions):
                    file_info['status'] = "Suspicious"
                else:
                    file_info['status'] = "Normal"
                
                results.append(file_info)
        
        # Check for files in quarantine
        if os.path.exists("safe_mtd"):
            for file in os.listdir("safe_mtd"):
                file_path = os.path.join("safe_mtd", file)
                if os.path.isfile(file_path):
                    results.append({
                        'path': file_path,
                        'status': "Quarantined"
                    })
        
        return results
    except Exception as e:
        print(f"Error scanning directory {directory_path}: {e}")
        return []
