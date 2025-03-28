import os
import sys
import time

# Common ransomware encrypted file extensions
RANSOMWARE_EXTENSIONS = ['.locked', '.crypt', '.encrypted', '.locky', '.crypted']

def analyze_directory():
    # Path to check
    test_data_path = 'test_data/'
    results_file_path = 'suspicious_files.txt'

    # Check if the directory exists
    if not os.path.exists(test_data_path):
        print(f"Directory {test_data_path} does not exist.")
        return False

    # Check if the directory is empty
    if check_directory_empty(test_data_path):
        print("Directory is empty, exiting with code 0.")
        return False
    else:
        # Check for ransomware indicators in the directory
        if check_for_ransomware(test_data_path, results_file_path):
            print("Ransomware detected, exiting with code 1.")
            return True
        else:
            print("No ransomware detected, exiting with code 0.")
            return False

def check_directory_empty(path):
    return not any(os.scandir(path))  # Return True if directory is empty

def check_for_ransomware(path, results_file_path):
    with open(results_file_path, 'w') as results_file:
        ransomware_detected = False
        # Go through each file in the directory
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)

                # Check file extension
                _, ext = os.path.splitext(file)
                if ext.lower() in RANSOMWARE_EXTENSIONS:
                    results_file.write(f"Suspicious file found: {file_path} (Extension: {ext})\n")
                    ransomware_detected = True

                # Check if file contents appear encrypted (non-readable text)
                if is_file_encrypted(file_path):
                    results_file.write(f"Encrypted file detected: {file_path}\n")
                    ransomware_detected = True

                # Check if the file was modified recently (within the last few minutes)
                if is_file_recently_modified(file_path):
                    results_file.write(f"Recently modified file: {file_path}\n")
                    ransomware_detected = True

    # Return True if any ransomware indicators were found
    return ransomware_detected

def is_file_encrypted(file_path):
    try:
        with open(file_path, 'rb') as f:
            # Read the first few bytes and check if it's readable ASCII text
            first_bytes = f.read(64)
            if not all(32 <= b <= 126 for b in first_bytes):  # Non-readable text found
                return True
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return False

def is_file_recently_modified(file_path):
    try:
        # Get the file modification time
        mod_time = os.path.getmtime(file_path)
        # Check if the file was modified in the last 10 minutes
        return (time.time() - mod_time) < 600
    except Exception as e:
        print(f"Error checking modification time for file {file_path}: {e}")
    return False

if __name__ == "__main__":
    result = analyze_directory()
    exit(0 if not result else 1)  # Exit code 0 for no ransomware, 1 for ransomware detected