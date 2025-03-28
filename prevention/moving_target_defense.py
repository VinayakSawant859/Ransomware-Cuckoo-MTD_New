import os
import shutil
import time
import logging

logging.basicConfig(filename='prevention/moving_target_defense.log', level=logging.INFO)

def rotate_file_paths():
    try:
        source_folder = 'test_data'
        target_folder = 'suspicious_mtd'
        extensions = ['.txt', '.crypt', '.locked', '.crypted', '.locky', '.encrypted']
        
        # List to keep track of moved files
        moved_files = []

        # Iterate through all files in the source folder
        for filename in os.listdir(source_folder):
            if any(filename.endswith(ext) for ext in extensions):
                original_file_path = os.path.join(source_folder, filename)
                # Change the extension to .txt
                # new_file_path = os.path.join(target_folder, f"suspicious_{int(time.time())}.txt")
                new_file_name = f"suspicious_{os.path.splitext(filename)[0]}.txt"
                new_file_path = os.path.join(target_folder, new_file_name)

                # Move the file
                shutil.move(original_file_path, new_file_path)
                moved_files.append((original_file_path, new_file_path))
                logging.info(f"Rotated file from {original_file_path} to {new_file_path}")

        if moved_files:
            return True, moved_files  # Return True and the list of moved files
        else:
            logging.warning("No files found to move.")
            return False, []  # Return False if no files were moved

    except Exception as e:
        logging.error(f"Error during MTD operation: {e}")
        return False, []  # Return False if there's an error

if __name__ == "__main__":
    result, moved_files = rotate_file_paths()
    if result:
        for source, destination in moved_files:
            print(f"MTD successfully applied from {source} to {destination}.")
    else:
        print("MTD failed.")