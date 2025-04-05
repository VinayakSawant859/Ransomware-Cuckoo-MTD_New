import os
import sys
import ctypes
import subprocess

def is_admin():
    """Check if the program is running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Launch the application with admin privileges using the virtual environment"""
    # Get the path to the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the virtual environment python executable
    venv_python = os.path.join(current_dir, "new_env", "Scripts", "python.exe")
    
    # Path to the main script
    main_script = os.path.join(current_dir, "main.py")
    
    if not os.path.exists(venv_python):
        print(f"Virtual environment not found at: {venv_python}")
        print("Make sure you have created the virtual environment named 'new_env'")
        input("Press Enter to exit...")
        return False
    
    if not os.path.exists(main_script):
        print(f"Main script not found at: {main_script}")
        print("Make sure you're running this script from the project root directory")
        input("Press Enter to exit...")
        return False
    
    # Construct the command to run the main script with the virtual environment python
    command = f'"{venv_python}" "{main_script}"'
    
    print(f"Launching with admin privileges: {command}")
    
    # Launch with admin privileges
    ctypes.windll.shell32.ShellExecuteW(None, "runas", venv_python, main_script, current_dir, 1)
    return True

def test_service():
    """Test the service directly without installing it"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(current_dir, "new_env", "Scripts", "python.exe")
    service_script = os.path.join(current_dir, "service", "detection_service.py")
    
    if not os.path.exists(venv_python):
        print("Virtual environment python not found.")
        return False
        
    if not os.path.exists(service_script):
        print("Service script not found.")
        return False
    
    print("Running service in test mode...")
    try:
        subprocess.run([venv_python, service_script, "test"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

if __name__ == "__main__":
    print("Ransomware Detection System Launcher")
    print("===================================")
    
    # Check for test mode
    if len(sys.argv) > 1 and sys.argv[1] == "test_service":
        if is_admin():
            test_service()
            input("Press Enter to exit...")
            sys.exit(0)
        else:
            print("Test mode requires administrator privileges.")
            print("Relaunching as administrator...")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, 
                f'"{os.path.abspath(__file__)}" test_service', None, 1
            )
            sys.exit(0)
    
    if is_admin():
        print("Already running with admin privileges.")
        print("Launching application directly...")
        try:
            # We're already admin, just import and run the app directly
            current_dir = os.path.dirname(os.path.abspath(__file__))
            venv_site_packages = os.path.join(current_dir, "new_env", "Lib", "site-packages")
            
            # Add the site-packages to sys.path if not already there
            if venv_site_packages not in sys.path:
                sys.path.insert(0, venv_site_packages)
            
            from splash_screen import SplashScreen
            from PyQt5.QtWidgets import QApplication
            
            app = QApplication(sys.argv)
            splash = SplashScreen()
            splash.show()
            sys.exit(app.exec_())
        except ImportError as e:
            print(f"Error importing modules: {e}")
            print("Make sure you have installed all dependencies in the virtual environment:")
            print("  new_env\\Scripts\\activate")
            print("  pip install -r requirements.txt")
            input("Press Enter to exit...")
    else:
        print("Launching application with admin privileges...")
        if run_as_admin():
            print("Admin launch request sent. This window will close.")
            # Wait a bit before closing
            import time
            time.sleep(2)
