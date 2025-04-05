import tkinter as tk
from tkinter import ttk
import time
from PIL import Image, ImageTk
import os
import sys
from main import RansomwareApp

class SplashScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position for center of screen
        splash_width = 600
        splash_height = 400
        x = (screen_width - splash_width) // 2
        y = (screen_height - splash_height) // 2
        
        self.root.geometry(f'{splash_width}x{splash_height}+{x}+{y}')
        
        # Create main frame with light theme
        self.frame = tk.Frame(self.root, bg='#ffffff')
        self.frame.place(relwidth=1, relheight=1)
        
        # Load and resize logo/background
        try:
            self.bg_image = Image.open("bg.jpg")
            self.bg_image = self.bg_image.resize((600, 400))
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_label = tk.Label(self.frame, image=self.bg_photo)
            self.bg_label.place(relwidth=1, relheight=1)
        except:
            # Fallback if image not found
            self.frame.configure(bg='#ffffff')

        # Create semi-transparent overlay
        self.overlay = tk.Frame(self.frame, bg='#ffffff')
        self.overlay.place(relwidth=1, relheight=1)
        self.overlay.configure(bg='#ffffff')
        
        # Welcome text with modern font
        self.title = tk.Label(
            self.overlay,
            text="Ransomware Detection & Prevention",
            font=('Helvetica', 24, 'bold'),
            fg='#333333',
            bg='#ffffff'
        )
        self.title.place(relx=0.5, rely=0.3, anchor='center')
        
        # Subtitle
        self.subtitle = tk.Label(
            self.overlay,
            text="Powered by Moving Target Defense",
            font=('Helvetica', 12),
            fg='#1976D2',
            bg='#ffffff'
        )
        self.subtitle.place(relx=0.5, rely=0.4, anchor='center')
        
        # Progress bar style
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#f0f0f0',
            background='#1976D2',
            thickness=4
        )
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.overlay,
            style="Custom.Horizontal.TProgressbar",
            length=400,
            mode='determinate'
        )
        self.progress.place(relx=0.5, rely=0.6, anchor='center')
        
        # Status text
        self.status = tk.Label(
            self.overlay,
            text="Initializing...",
            font=('Helvetica', 10),
            fg='#888888',
            bg='#ffffff'
        )
        self.status.place(relx=0.5, rely=0.7, anchor='center')
        
        # Start loading animation
        self.progress_value = 0
        self.load_animation()

    def load_animation(self):
        if self.progress_value < 100:
            self.progress_value += 1
            self.progress['value'] = self.progress_value
            
            # Update status text based on progress
            if self.progress_value < 30:
                self.status['text'] = "Loading components..."
            elif self.progress_value < 60:
                self.status['text'] = "Initializing security modules..."
            elif self.progress_value < 90:
                self.status['text'] = "Starting application..."
            else:
                self.status['text'] = "Ready to launch..."
            
            self.root.after(30, self.load_animation)
        else:
            self.root.after(500, self.launch_main_app)

    def launch_main_app(self):
        root = tk.Tk()  # Create new root window
        root.withdraw()  # Hide it initially
        
        # Destroy splash screen
        self.root.destroy()
        
        # Create and show role selection window
        from components.welcome_page import WelcomePage
        welcome = WelcomePage(root)
        
        # Start main event loop
        root.mainloop()

if __name__ == "__main__":
    splash = SplashScreen()
    splash.root.mainloop()