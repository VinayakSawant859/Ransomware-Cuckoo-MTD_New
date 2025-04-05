import tkinter as tk
from .login import LoginWindow

class WelcomePage:
    def __init__(self, root):
        self.root = root
        
        # Window setup
        self.window = tk.Toplevel(root)
        self.window.title("Welcome")
        self.window.geometry("500x600")
        self.window.configure(bg='#ffffff')
        
        # Ensure this window stays on top
        self.window.focus_force()
        self.window.grab_set()
        
        # Make window modal and prevent closing
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.transient(root)
        self.window.grab_set()
        
        # Center window
        self.center_window(500, 600)
        
        # Title
        title = tk.Label(
            self.window,
            text="Welcome to\nRansomware Detection System",
            font=('Helvetica', 24, 'bold'),
            bg='#ffffff',
            fg='#333333',
            justify='center'
        )
        title.pack(pady=50)
        
        # Buttons frame
        buttons_frame = tk.Frame(self.window, bg='#ffffff')
        buttons_frame.pack(pady=30)
        
        # Common button style
        button_style = {
            'font': ('Helvetica', 14, 'bold'),
            'width': 25,
            'height': 2,
            'relief': tk.FLAT,
            'cursor': 'hand2'
        }
        
        # Student button
        self.student_btn = tk.Button(
            buttons_frame,
            text="Login as Student",
            bg='#2196F3',
            fg='white',
            command=self.show_student_login,
            **button_style
        )
        self.student_btn.pack(pady=15)
        
        # Faculty button
        self.faculty_btn = tk.Button(
            buttons_frame,
            text="Login as Faculty",
            bg='#4CAF50',
            fg='white',
            command=self.show_faculty_login,
            **button_style
        )
        self.faculty_btn.pack(pady=15)
        
        # Admin button
        self.admin_btn = tk.Button(
            buttons_frame,
            text="Login as Admin",
            bg='#FF5722',
            fg='white',
            command=self.show_admin_login,
            **button_style
        )
        self.admin_btn.pack(pady=15)
        
        # Bind hover events
        for btn, color in [
            (self.student_btn, '#1976D2'),
            (self.faculty_btn, '#388E3C'),
            (self.admin_btn, '#D84315')
        ]:
            self._bind_hover_events(btn, btn.cget('bg'), color)

    def center_window(self, width, height):
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def _bind_hover_events(self, button, default_color, hover_color):
        button.bind('<Enter>', lambda e: e.widget.config(bg=hover_color))
        button.bind('<Leave>', lambda e: e.widget.config(bg=default_color))

    def show_student_login(self):
        self.window.withdraw()
        LoginWindow(self.root, self.on_login_success, 'student', self.show_window)
        
    def show_faculty_login(self):
        self.window.withdraw()
        LoginWindow(self.root, self.on_login_success, 'faculty', self.show_window)
        
    def show_admin_login(self):
        self.window.withdraw()
        LoginWindow(self.root, self.on_login_success, 'admin', self.show_window)

    def show_window(self):
        self.window.deiconify()

    def on_login_success(self, user_email, user_role):
        # Properly initialize main window before creating RansomwareApp
        self.window.destroy()
        self.root.deiconify()
        
        # Create new root for main application
        main_root = tk.Tk()
        main_root.withdraw()  # Hide temporarily
        
        # Initialize main application with user info
        from main import RansomwareApp
        app = RansomwareApp(main_root, user_email, user_role)
        
        # Close old root and show main application
        self.root.destroy()
        main_root.deiconify()

    def on_closing(self):
        self.root.quit()  # This will close the entire application
