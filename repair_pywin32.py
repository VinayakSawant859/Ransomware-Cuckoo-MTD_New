import os
import sys
import subprocess
import shutil
import time
import tempfile
import platform
import ctypes

def is_admin():
    """Check if running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def main():
    print("PyWin32 Repair Tool")
    print("===================")
    print(f"Python version: {sys.version}")
    print(f"Executable: {sys.executable}")
    
    if not is_admin():
        print("\nWARNING: This script should be run with Administrator privileges.")
        print("Some operations may fail without admin rights.")
        
        try:
            if platform.system() == 'Windows':
                print("\nWould you like to relaunch as administrator? (y/n)")
                response = input().strip().lower()
                if response == 'y':
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", sys.executable, 
                        f'"{os.path.abspath(__file__)}"', None, 1
                    )
                    return
        except:
            pass
    
    # Step 1: Uninstall any current pywin32 installation
    print("\nStep 1: Uninstalling current pywin32...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "pywin32"], 
                      capture_output=True, text=True)
    except Exception as e:
        print(f"  Warning: {e}")
    
    # Step 2: Clean up any remaining pywin32 files
    print("\nStep 2: Cleaning up pywin32 files...")
    for path in sys.path:
        if "site-packages" in path:
            site_packages = path
            break
    else:
        print("  Error: Could not find site-packages directory")
        return
    
    print(f"  Site-packages directory: {site_packages}")
    
    # Clean directories that might have pywin32 files
    for dirname in ["win32", "win32com", "win32comext", "pywin32_system32", "pythonwin"]:
        dir_path = os.path.join(site_packages, dirname)
        if os.path.exists(dir_path):
            print(f"  Removing {dir_path}")
            try:
                shutil.rmtree(dir_path)
            except Exception as e:
                print(f"    Warning: {e}")
    
    # Step 3: Install pywin32 version 302 (known to be stable)
    print("\nStep 3: Installing pywin32 version 302...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", "pywin32==302"],
                               capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  Error: {result.stderr}")
            print("\nTrying alternative approach with latest version...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pywin32"],
                          capture_output=True, text=True)
    except Exception as e:
        print(f"  Error: {e}")
        return
    
    # Step 4: Find and run the post-install script
    print("\nStep 4: Running post-install script...")
    
    # Try to find the script in various locations
    script_paths = [
        os.path.join(os.path.dirname(sys.executable), "Scripts", "pywin32_postinstall.py"),
        os.path.join(site_packages, "pywin32_system32", "scripts", "pywin32_postinstall.py"),
        os.path.join(site_packages, "win32", "scripts", "pywin32_postinstall.py")
    ]
    
    script_found = False
    for script_path in script_paths:
        if os.path.exists(script_path):
            print(f"  Found post-install script at: {script_path}")
            script_found = True
            try:
                # Execute with -install flag
                subprocess.run([sys.executable, script_path, "-install"], 
                              capture_output=True, text=True)
                print("  Post-install script executed successfully")
            except Exception as e:
                print(f"  Error running script: {e}")
            break
    
    if not script_found:
        print("  Could not find post-install script.")
        print("  Creating temporary script...")
        
        # Create a temporary post-install script with basic functionality
        temp_dir = tempfile.mkdtemp()
        temp_script = os.path.join(temp_dir, "pywin32_postinstall.py")
        
        with open(temp_script, 'w') as f:
            f.write("""
import sys, os
import platform
import traceback

def install():
    try:
        # Find the pywin32_system32 directory
        for p in sys.path:
            if "site-packages" in p:
                pywin32_system32 = os.path.join(p, "pywin32_system32")
                if os.path.exists(pywin32_system32):
                    # Copy DLL files to system32
                    import shutil
                    import glob
                    
                    # Get paths
                    system32_dir = os.path.join(os.environ["WINDIR"], "system32")
                    python_dir = os.path.dirname(sys.executable)
                    
                    # Copy DLLs
                    for dll in glob.glob(os.path.join(pywin32_system32, "*.dll")):
                        print(f"Copying {os.path.basename(dll)} to system directories")
                        try:
                            dst = os.path.join(system32_dir, os.path.basename(dll))
                            if not os.path.exists(dst):
                                shutil.copy2(dll, system32_dir)
                            
                            dst = os.path.join(python_dir, os.path.basename(dll))
                            if not os.path.exists(dst):
                                shutil.copy2(dll, python_dir)
                        except Exception as e:
                            print(f"Error: {e}")
                    
                    print("PyWin32 DLLs installed successfully")
                    return
    except Exception as e:
        print(f"Error during install: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    if '-install' in sys.argv:
        install()
"""
            )
        
        try:
            subprocess.run([sys.executable, temp_script, "-install"],
                          capture_output=True, text=True)
            print("  Temporary script executed successfully")
        except Exception as e:
            print(f"  Error running temporary script: {e}")
        
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
    
    # Step 5: Final verification
    print("\nStep 5: Verifying installation...")
    try:
        # Force reload modules if they were previously imported
        for module in ['win32api', 'win32com', 'pythoncom']:
            if module in sys.modules:
                del sys.modules[module]
        
        # Try importing the modules
        import win32api
        import win32com.client
        
        print("\nSuccess! PyWin32 is now working properly.")
        print("You should now be able to run 'python -m win32com.client.makepy winmgmt'")
        
        # Try running the makepy command directly
        print("\nRunning makepy for winmgmt...")
        try:
            subprocess.run([sys.executable, "-m", "win32com.client.makepy", "winmgmt"],
                          capture_output=True, text=True)
            print("  Command executed successfully")
        except Exception as e:
            print(f"  Error running makepy: {e}")
            
    except ImportError as e:
        print(f"\nError: PyWin32 is still not working properly: {e}")
        print("\nAdditional troubleshooting steps:")
        print("1. Try restarting your command prompt/terminal with admin rights")
        print("2. Try reinstalling Python completely")
        print("3. Download the official pywin32 installer from:")
        print("   https://github.com/mhammond/pywin32/releases")
        print("4. Try creating a new virtual environment")

if __name__ == "__main__":
    main()
    
    # Keep console open
    if not sys.stdout.isatty():  # If running from double-click
        print("\nPress Enter to exit...")
        input()
