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
    """Re-launch the program with admin rights"""
    script = os.path.abspath(sys.argv[0])
    params = ' '.join([f'"{item}"' for item in sys.argv[1:]])
    
    if script.endswith('.py'):
        # If running as a Python script, use the interpreter
        python_exe = sys.executable
        cmd = f'"{python_exe}" "{script}" {params}'
    else:
        # If running as exe
        cmd = f'"{script}" {params}'
    
    # Launch process with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, cmd, None, 1)

if __name__ == '__main__':
    if not is_admin():
        print("Relaunching with administrator privileges...")
        run_as_admin()
        sys.exit(0)
    else:
        # We're running as admin, import and run the main app
        try:
            from splash_screen import SplashScreen
            from PyQt5.QtWidgets import QApplication
            
            app = QApplication(sys.argv)
            splash = SplashScreen()
            splash.show()
            sys.exit(app.exec_())
        except ImportError:
            print("Error: Could not import required modules.")
            print("Make sure you have PyQt5 installed: pip install PyQt5")
            input("Press Enter to exit...")
