# Ransomware Cuckoo-MTD

Follow these steps to set up the project:

1. **Download the Project**

   - Download the ZIP file of the project and extract it to your desired location.

2. **Create a Virtual Environment**
   - Open a terminal in VS Code

   - Navigate to the project directory

   - Open Terminal

   - Create a new virtual environment:

     python -m venv new_env


3. **Activate the Virtual Environment**

     new_env\Scripts\activate

4. **Install Required Packages**

   - Install the necessary packages using `pip`:

     pip install -r requirements.txt


5. **Run the Application**

   - Start the application by running:

     python welcome_page.py

## Running the Application

### Administrator Privileges Required

This application requires administrator privileges to install and manage Windows services for:
- Background ransomware detection
- File system monitoring
- Moving Target Defense operations

### Running as Administrator

#### Method 1: Using the virtual environment launcher (Recommended)
1. Navigate to the application folder
2. Right-click on `run_env_as_admin.py` and select "Run with Python"
3. Accept the User Account Control (UAC) prompt

This launcher will automatically use your `new_env` virtual environment with admin privileges.

#### Method 2: For the standard launcher
1. Navigate to the application folder
2. Find the file `run_as_admin.py`
3. Right-click on it and select "Run with Python"
4. Accept the User Account Control (UAC) prompt

#### Method 3: Using Command Prompt
1. Open Command Prompt as administrator
   - Press Windows key
   - Type "cmd"
   - Right-click on "Command Prompt"
   - Select "Run as administrator"
2. Navigate to application folder
3. Activate the environment and run the app:
   ```
   new_env\Scripts\activate
   python main.py
   ```

## Troubleshooting

If you encounter service installation issues, verify that:
1. You're running the application with administrator privileges
2. Windows service management is functioning properly
3. Python and PyWin32 are correctly installed: `pip install pywin32` in your virtual environment
4. If you get import errors, make sure all required packages are installed in your virtual environment
