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
        
        # Create main frame with dark theme
        self.frame = tk.Frame(self.root, bg='#1c1c1c')
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
            self.frame.configure(bg='#1c1c1c')

        # Create semi-transparent overlay
        self.overlay = tk.Frame(self.frame, bg='#1c1c1c')
        self.overlay.place(relwidth=1, relheight=1)
        self.overlay.configure(bg='#1c1c1c')
        
        # Welcome text with modern font
        self.title = tk.Label(
            self.overlay,
            text="Ransomware Detection & Prevention",
            font=('Helvetica', 24, 'bold'),
            fg='white',
            bg='#1c1c1c'
        )
        self.title.place(relx=0.5, rely=0.3, anchor='center')
        
        # Subtitle
        self.subtitle = tk.Label(
            self.overlay,
            text="Powered by Moving Target Defense",
            font=('Helvetica', 12),
            fg='#0056A0',
            bg='#1c1c1c'
        )
        self.subtitle.place(relx=0.5, rely=0.4, anchor='center')
        
        # Progress bar style
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#1c1c1c',
            background='#0056A0',
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
            bg='#1c1c1c'
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
        self.root.destroy()
        root = tk.Tk()
        app = RansomwareApp(root)
        root.mainloop()

if __name__ == "__main__":
    splash = SplashScreen()
    splash.root.mainloop()