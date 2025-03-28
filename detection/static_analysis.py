import pefile
import logging

logging.basicConfig(filename='detection/static_analysis.log', level=logging.INFO)

def analyze_file(file_path):
    pe = pefile.PE(file_path)
    logging.info(f"File: {file_path}, Entry Point: {hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)}")
    if "ransomware" in file_path.lower():  # Example condition for detection
        return True
    return False

if __name__ == "__main__":
    result = analyze_file('C:\\Windows\\System32\\cmd.exe')  # Provide the path to the file you want to analyze
    exit(0 if not result else 1)  # Exit 0 for no ransomware, 1 for ransomware detected
