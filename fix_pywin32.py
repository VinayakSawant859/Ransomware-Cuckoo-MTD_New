import os
import sys
import subprocess
import platform
import shutil
import glob
import time
import traceback

def fix_pywin32():
    """Fix PyWin32 installation by running the post-install script"""
    print("PyWin32 Fix Utility (Enhanced)")
    print("=============================")
    print(f"Python Version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print()
    
    # Find the Python installation directory
    python_path = sys.executable
    print(f"Python executable: {python_path}")
    
    # Get the site-packages directory
    site_packages = None
    for path in sys.path:
        if "site-packages" in path:
            site_packages = path
            break
    
    if not site_packages:
        print("Error: Could not find site-packages directory")
        return False
    
    print(f"Site-packages directory: {site_packages}")
    
    # Try several fix methods in sequence
    if try_direct_copy_method(python_path, site_packages):
        print("Direct copy method successful!")
        return True
    
    if try_postinstall_script(python_path, site_packages):
        print("Post-install script method successful!")
        return True
    
    if try_reinstall_method(python_path, site_packages):
        print("Reinstall method successful!")
        return True
    
    if try_manual_registration(site_packages):
        print("Manual registration successful!")
        return True
    
    print("\nAll automated fix attempts failed.")
    return False

def try_direct_copy_method(python_path, site_packages):
    """Try fixing by directly copying DLL files"""
    try:
        print("\n[Method 1] Attempting direct DLL copy method...")
        
        # Find all possible DLL locations
        win32_dll_dirs = [
            os.path.join(site_packages, "pywin32_system32"),
            os.path.join(site_packages, "win32", "lib"),
            os.path.join(os.path.dirname(python_path), "Lib", "site-packages", "pywin32_system32")
        ]
        
        # Target directories to copy to
        target_dirs = [
            os.path.dirname(python_path),  # Python dir
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'System32'),  # Windows System32
        ]
        
        # Try to find and copy needed DLLs
        dlls_copied = False
        for dll_dir in win32_dll_dirs:
            if os.path.exists(dll_dir):
                print(f"Found DLL directory: {dll_dir}")
                dll_files = glob.glob(os.path.join(dll_dir, "*.dll"))
                pyd_files = glob.glob(os.path.join(site_packages, "win32", "*.pyd"))
                
                print(f"Found {len(dll_files)} DLL files and {len(pyd_files)} PYD files")
                
                # Copy DLLs to Python directory
                for src in dll_files:
                    for target_dir in target_dirs:
                        if os.access(target_dir, os.W_OK):  # Check if we have write permissions
                            dst = os.path.join(target_dir, os.path.basename(src))
                            try:
                                print(f"Copying {src} to {dst}")
                                shutil.copy2(src, dst)
                                dlls_copied = True
                            except Exception as e:
                                print(f"  Error copying: {e}")
                
                # If we copied any DLLs, let's stop here
                if dlls_copied:
                    break
        
        if not dlls_copied:
            print("Could not copy any DLL files - permission issues or DLLs not found")
            return False
            
        # Test if win32api can be imported now
        print("\nTesting PyWin32 import after DLL copy...")
        try:
            # Add small delay to ensure files are properly registered
            time.sleep(1)
            
            # Force reload of any previously failed imports
            if 'win32api' in sys.modules:
                del sys.modules['win32api']
            if 'win32com' in sys.modules:
                del sys.modules['win32com']
                
            import win32api
            import win32com.client
            print("Success! PyWin32 is now working properly.")
            return True
        except ImportError as e:
            print(f"Import still fails after DLL copy: {e}")
            return False
    except Exception as e:
        print(f"Error in direct copy method: {e}")
        print(traceback.format_exc())
        return False

def try_postinstall_script(python_path, site_packages):
    """Try fixing by running the pywin32 post-install script"""
    try:
        print("\n[Method 2] Attempting to run post-install script...")
        
        # Find pywin32_postinstall.py in various possible locations
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(site_packages)), "Scripts")
        possible_script_locations = [
            os.path.join(scripts_dir, "pywin32_postinstall.py"),
            os.path.join(site_packages, "win32", "scripts", "pywin32_postinstall.py"),
            os.path.join(site_packages, "pywin32_postinstall.py"),
            os.path.join(os.path.dirname(python_path), "Scripts", "pywin32_postinstall.py")
        ]
        
        postinstall_script = None
        for loc in possible_script_locations:
            if os.path.exists(loc):
                postinstall_script = loc
                print(f"Found post-install script at: {loc}")
                break
        
        if not postinstall_script:
            print("Could not find pywin32_postinstall.py script")
            return False
        
        print(f"Running post-install script: {postinstall_script}")
        try:
            # Run with -install flag
            subprocess.check_call([python_path, postinstall_script, "-install"])
            print("Post-install script completed successfully")
            
            # Test again
            print("\nTesting PyWin32 import after post-install...")
            try:
                # Force reload of any previously failed imports
                if 'win32api' in sys.modules:
                    del sys.modules['win32api']
                if 'win32com' in sys.modules:
                    del sys.modules['win32com']
                    
                import win32api
                import win32com.client
                print("Success! PyWin32 is now working properly.")
                return True
            except ImportError as e:
                print(f"Import still fails after post-install: {e}")
                return False
        except subprocess.CalledProcessError as e:
            print(f"Error running post-install script: {e}")
            return False
    except Exception as e:
        print(f"Error in post-install script method: {e}")
        print(traceback.format_exc())
        return False

def try_reinstall_method(python_path, site_packages):
    """Try fixing by completely reinstalling pywin32"""
    try:
        print("\n[Method 3] Attempting complete reinstallation of pywin32...")
        
        # Uninstall first
        print("Uninstalling pywin32...")
        try:
            subprocess.check_call([python_path, "-m", "pip", "uninstall", "-y", "pywin32"])
        except:
            print("Error uninstalling or package not found - continuing...")
        
        # Install specific version known to work well
        print("Installing pywin32 version 302...")
        try:
            subprocess.check_call([python_path, "-m", "pip", "install", "pywin32==302"])
        except subprocess.CalledProcessError as e:
            print(f"Error installing pywin32==302: {e}")
            
            # Try latest version as fallback
            print("Trying latest version instead...")
            try:
                subprocess.check_call([python_path, "-m", "pip", "install", "pywin32"])
            except subprocess.CalledProcessError as e2:
                print(f"Error installing latest pywin32: {e2}")
                return False
        
        # Run post-install script if found
        post_install_path = os.path.join(os.path.dirname(python_path), "Scripts", "pywin32_postinstall.py")
        if os.path.exists(post_install_path):
            print(f"Running post-install script after reinstall: {post_install_path}")
            try:
                subprocess.check_call([python_path, post_install_path, "-install"])
            except:
                print("Error running post-install script after reinstall")
        
        # Test after reinstall
        print("\nTesting PyWin32 import after reinstall...")
        try:
            # Force reload
            if 'win32api' in sys.modules:
                del sys.modules['win32api']
            if 'win32com' in sys.modules:
                del sys.modules['win32com']
                
            import win32api
            import win32com.client
            print("Success! PyWin32 is now working properly.")
            return True
        except ImportError as e:
            print(f"Import still fails after reinstall: {e}")
            return False
    except Exception as e:
        print(f"Error in reinstall method: {e}")
        print(traceback.format_exc())
        return False

def try_manual_registration(site_packages):
    """Try manual registration of DLLs using Windows regsvr32"""
    try:
        print("\n[Method 4] Attempting manual DLL registration...")
        
        # Find all DLLs
        win32_dll_dirs = [
            os.path.join(site_packages, "pywin32_system32"),
            os.path.join(site_packages, "win32", "lib"),
            os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages", "pywin32_system32")
        ]
        
        dlls_registered = False
        for dll_dir in win32_dll_dirs:
            if os.path.exists(dll_dir):
                print(f"Found DLL directory: {dll_dir}")
                dll_files = glob.glob(os.path.join(dll_dir, "*.dll"))
                
                # Register DLLs using regsvr32
                for dll in dll_files:
                    print(f"Registering {dll}")
                    try:
                        subprocess.check_call(["regsvr32", "/s", dll])
                        dlls_registered = True
                    except:
                        print(f"  Failed to register {dll}")
        
        if not dlls_registered:
            print("No DLLs were successfully registered")
            return False
        
        # Test again
        print("\nTesting PyWin32 import after manual registration...")
        try:
            # Force reload
            if 'win32api' in sys.modules:
                del sys.modules['win32api']
            if 'win32com' in sys.modules:
                del sys.modules['win32com']
                
            import win32api
            import win32com.client
            print("Success! PyWin32 is now working properly.")
            return True
        except ImportError as e:
            print(f"Import still fails after manual registration: {e}")
            return False
    except Exception as e:
        print(f"Error in manual registration method: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Check if running as administrator
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        # Windows doesn't have getuid, so try windows-specific check
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            is_admin = False
    
    if not is_admin:
        print("WARNING: This script should ideally be run with administrator privileges.")
        print("Some operations may fail without admin rights.")
        
        # We can offer to relaunch as admin
        try:
            if platform.system() == 'Windows':
                print("\nWould you like to relaunch as administrator? (y/n)")
                response = input().strip().lower()
                if response == 'y':
                    print("Relaunching with admin privileges...")
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", sys.executable, 
                        f'"{os.path.abspath(__file__)}"', None, 1
                    )
                    sys.exit(0)
        except:
            pass
        
        print("Continuing without admin privileges...")
    
    # Run the fix
    if fix_pywin32():
        print("\nFix completed successfully! Try running your command again.")
        print("You may need to restart your command prompt or IDE.")
    else:
        print("\nFix attempts failed. Here are some additional steps to try:")
        print("1. Run this script as administrator (if you haven't already)")
        print("2. Try installing using the official installer from:")
        print("   https://github.com/mhammond/pywin32/releases")
        print("3. Consider creating a fresh virtual environment")
        print("4. You may need to restart your computer after fixes")
    
    # Keep console open
    if platform.system() == 'Windows':
        print("\nPress Enter to exit...")
        input()
