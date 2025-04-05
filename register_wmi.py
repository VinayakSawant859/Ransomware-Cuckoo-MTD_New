import os
import sys
import subprocess
import platform
import time
import ctypes

def is_admin():
    """Check if running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def register_wmi_typelib():
    """Register the WMI type library specifically"""
    print("WMI TypeLib Registration Utility")
    print("================================")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print()
    
    try:
        # First try direct approach using makepy with the specific ProgID
        print("Attempting to register WMI typelib...")
        
        # These are the common WMI typelib identifiers
        typelibs = [
            "{565783C6-CB41-11D1-8B02-00600806D9B6}", # WMI Scripting
            "{76A64158-CB41-11D1-8B02-00600806D9B6}", # WBEM Scripting
            "Microsoft WMI Scripting",
            "WbemScripting.SWbemLocator"
        ]
        
        success = False
        
        for typelib in typelibs:
            print(f"\nTrying to register: {typelib}")
            try:
                # Use the makepy command with specific typelib
                result = subprocess.run(
                    [sys.executable, "-m", "win32com.client.makepy", typelib],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"Successfully registered typelib: {typelib}")
                    success = True
                else:
                    print(f"Registration failed: {result.stderr.strip()}")
            except Exception as e:
                print(f"Error running makepy: {e}")
        
        if not success:
            # Try a more direct approach - create a script to instantiate WMI
            print("\nAttempting alternative WMI registration approach...")
            
            temp_script = "temp_wmi_reg.py"
            with open(temp_script, "w") as f:
                f.write("""
import sys
import win32com.client
import win32com.client.gencache

# Try to generate from the SWbemLocator
try:
    locator = win32com.client.Dispatch("WbemScripting.SWbemLocator")
    win32com.client.gencache.EnsureModule('{76A64158-CB41-11D1-8B02-00600806D9B6}', 0, 1, 0)
    print("WbemScripting.SWbemLocator registered successfully")
except Exception as e:
    print(f"Error with SWbemLocator: {e}")

# Try to directly connect to WMI
try:
    wmi = win32com.client.GetObject("winmgmts:")
    print("Connected to WMI service")
except Exception as e:
    print(f"Error connecting to WMI: {e}")
""")
            
            try:
                result = subprocess.run([sys.executable, temp_script], capture_output=True, text=True)
                print(result.stdout)
                
                if "successfully" in result.stdout or "Connected to WMI service" in result.stdout:
                    success = True
            except Exception as e:
                print(f"Error running alternative approach: {e}")
            
            # Clean up temp file
            try:
                os.remove(temp_script)
            except:
                pass
        
        if success:
            print("\nWMI typelib registration completed successfully!")
            print("You should now be able to run: python -m win32com.client.makepy winmgmt")
            
            # Try the original command again to verify
            print("\nVerifying with original command...")
            try:
                verify_result = subprocess.run(
                    [sys.executable, "-m", "win32com.client.makepy", "winmgmt"],
                    capture_output=True,
                    text=True
                )
                
                if verify_result.returncode == 0:
                    print("\nSuccess! winmgmt typelib registered correctly.")
                else:
                    print("\nVerification failed. However, WMI may still be usable.")
                    print("Try using the WMI interfaces directly in your code.")
            except Exception as e:
                print(f"\nError during verification: {e}")
        else:
            print("\nWMI registration was not successful.")
            print("Consider trying these alternatives:")
            print("1. Use the WMI module instead: pip install wmi")
            print("2. Use native WMI queries in PowerShell")
            print("3. Try different COM registration tools")
            
        return success
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def check_wmi_service():
    """Check if the WMI service is running"""
    try:
        print("\nChecking WMI service status...")
        result = subprocess.run(
            ["sc", "query", "Winmgmt"], 
            capture_output=True, 
            text=True
        )
        
        if "RUNNING" in result.stdout:
            print("WMI service is running.")
            return True
        else:
            print("WMI service is not running. Attempting to start it...")
            start_result = subprocess.run(
                ["sc", "start", "Winmgmt"],
                capture_output=True,
                text=True
            )
            
            if start_result.returncode == 0:
                print("WMI service started successfully. Waiting for initialization...")
                time.sleep(3)  # Give it time to initialize
                return True
            else:
                print(f"Failed to start WMI service: {start_result.stderr}")
                return False
    except Exception as e:
        print(f"Error checking WMI service: {e}")
        return False

if __name__ == "__main__":
    if not is_admin() and platform.system() == 'Windows':
        print("This script should be run with administrator privileges for best results.")
        print("Would you like to relaunch as administrator? (y/n)")
        response = input().strip().lower()
        
        if response == 'y':
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, 
                f'"{os.path.abspath(__file__)}"', None, 1
            )
            sys.exit(0)
        else:
            print("Continuing without admin privileges...")
    
    check_wmi_service()
    register_wmi_typelib()
    
    # Keep console window open if not in interactive mode
    if not sys.stdout.isatty():  # Running from double-click
        print("\nPress Enter to exit...")
        input()
