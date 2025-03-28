import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import subprocess
import os
from reports.generate_report import generate_report
from prevention.moving_target_defense import rotate_file_paths
from tkinter import Label
import time
import threading
import math
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText

# Set matplotlib backend
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class RansomwareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ransomware Detection and Prevention")
        self.root.geometry("1536x864")

        # Load icons
        self.virus_icon = tk.PhotoImage(file="drawable/icons8-virus-file-24.png")
        self.lock_icon = tk.PhotoImage(file="drawable/icons8-lock-50.png")
        self.shield_icon = tk.PhotoImage(file="drawable/icons8-shield-50.png")

        # Load and set the background image
        self.bg_image = Image.open("bg.jpg")
        self.bg_image = self.bg_image.resize((1536, 864))
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)

        self.bg_label = Label(root, image=self.bg_photo)
        self.bg_label.place(relwidth=1, relheight=1)

        # Modern theme colors
        self.bg_color = '#1c1c1c'
        self.frame_bg_color = '#1c1c1c'
        self.button_color = '#0056A0'
        self.button_fg_color = 'white'
        self.label_fg_color = 'white'
        self.status_fg_color = 'lightgreen'
        self.error_fg_color = 'red'

        # Create main frame
        self.main_frame = tk.Frame(root, bg=self.bg_color)
        self.main_frame.place(relwidth=1, relheight=1)

        # Project Title
        self.title_label = tk.Label(
            self.main_frame,
            text="Ransomware Detection and Prevention",
            font=('Helvetica', 24, 'bold'),
            bg=self.bg_color,
            fg=self.label_fg_color,
            pady=20
        )
        self.title_label.pack()

        # Configure ttk styles
        self.style = ttk.Style()
        self.style.theme_use('default')

        # Configure the notebook style
        self.style.configure(
            "Custom.TNotebook",
            background=self.bg_color,
            borderwidth=0,
            tabmargins=[2, 5, 2, 0]
        )
        
        self.style.configure(
            "Custom.TNotebook.Tab",
            padding=[20, 10],
            background='#2c2c2c',
            foreground='white',
            font=('Helvetica', 12, 'bold'),
            borderwidth=0
        )
        
        self.style.map(
            "Custom.TNotebook.Tab",
            background=[("selected", '#0056A0'), ("active", '#004080')],
            foreground=[("selected", 'white'), ("active", 'white')]
        )

        # Configure frame style
        self.style.configure(
            'Custom.TFrame',
            background=self.frame_bg_color
        )

        # Create notebook
        self.notebook = ttk.Notebook(
            self.main_frame,
            style="Custom.TNotebook"
        )
        self.notebook.pack(fill='both', expand=True, padx=20, pady=20)

        # Create frames for each tab
        self.detection_frame = tk.Frame(self.notebook, bg=self.frame_bg_color)
        self.prevention_frame = tk.Frame(self.notebook, bg=self.frame_bg_color)
        self.report_frame = tk.Frame(self.notebook, bg=self.frame_bg_color)
        self.exit_frame = tk.Frame(self.notebook, bg=self.frame_bg_color)  # New exit frame

        # Add frames to notebook
        self.notebook.add(self.detection_frame, text="Detection")
        self.notebook.add(self.prevention_frame, text="Prevention")
        self.notebook.add(self.report_frame, text="Generate Report")
        self.notebook.add(self.exit_frame, text="Exit")  # Add exit tab

        # Initialize tab contents
        self.setup_detection_tab()
        self.setup_prevention_tab()
        self.setup_report_tab()
        self.setup_exit_tab()  # Setup exit tab

    def setup_detection_tab(self):
        # Create a container frame with padding
        container = tk.Frame(
            self.detection_frame,
            bg=self.frame_bg_color,
            padx=30,
            pady=20
        )
        container.pack(fill='both', expand=True)

        # Info Label with enhanced styling
        info_label = tk.Label(
            container,
            text="Monitor and detect potential ransomware activities",
            font=('Helvetica', 18, 'bold'),
            bg=self.frame_bg_color,
            fg='#e0e0e0',
            wraplength=800,
            justify="center"
        )
        info_label.pack(pady=(20, 40))

        # Create button frame for hover effect
        button_frame = tk.Frame(container, bg=self.frame_bg_color)
        button_frame.pack(pady=(0, 30))

        # Start Detection Button with hover effect
        self.start_detection_btn = tk.Button(
            button_frame,
            text="Start Detection",
            command=self.start_detection,
            bg=self.button_color,
            fg=self.button_fg_color,
            font=('Helvetica', 14, 'bold'),
            relief=tk.FLAT,
            borderwidth=0,
            width=20,
            cursor="hand2"
        )
        self.start_detection_btn.pack(pady=10)

        # Bind hover events
        self.start_detection_btn.bind('<Enter>', lambda e: e.widget.config(bg='#0066CC'))
        self.start_detection_btn.bind('<Leave>', lambda e: e.widget.config(bg=self.button_color))

        # Loading animation canvas (hidden initially)
        self.loading_canvas = tk.Canvas(
            container,
            width=100,  # Increased size
            height=100,  # Increased size
            bg=self.frame_bg_color,
            highlightthickness=0
        )
        self.loading_canvas.pack_forget()

        # Plot Frame with border
        self.plot_frame = tk.Frame(
            container,
            bg=self.frame_bg_color,
            relief=tk.SOLID,
            borderwidth=1,
            highlightbackground='#404040',
            highlightthickness=1
        )
        self.plot_frame.pack(pady=20, fill=tk.BOTH, expand=True)

        # Labels Frame
        labels_frame = tk.Frame(container, bg=self.frame_bg_color)
        labels_frame.pack(fill='x', pady=10)

        # Severity Label with enhanced styling
        self.severity_label = tk.Label(
            labels_frame,
            text="",
            font=('Helvetica', 14, 'bold'),
            bg=self.frame_bg_color,
            fg=self.label_fg_color
        )
        self.severity_label.pack(pady=5)

        # Recently Detected Label
        self.recently_detected_label = tk.Label(
            labels_frame,
            text="",
            font=('Helvetica', 12, 'bold'),
            bg=self.frame_bg_color,
            fg='#0056A0'
        )
        self.recently_detected_label.pack(pady=5)

        # Suspicious Files Label
        self.suspicious_files_label = tk.Label(
            labels_frame,
            text="",
            font=('Helvetica', 11),
            bg=self.frame_bg_color,
            fg=self.label_fg_color
        )
        self.suspicious_files_label.pack(pady=5)

    def setup_prevention_tab(self):
        # Create container frame
        container = tk.Frame(
            self.prevention_frame,
            bg=self.frame_bg_color,
            padx=30,
            pady=20
        )
        container.pack(fill='both', expand=True)

        # Info Label with icon
        info_frame = tk.Frame(container, bg=self.frame_bg_color)
        info_frame.pack(pady=(0, 30))
        
        # Shield icon label
        icon_label = tk.Label(
            info_frame,
            image=self.shield_icon,
            bg=self.frame_bg_color
        )
        icon_label.pack(pady=(0, 10))

        info_label = tk.Label(
            info_frame,
            text="Implement Moving Target Defense to prevent ransomware attacks",
            font=('Helvetica', 18, 'bold'),
            bg=self.frame_bg_color,
            fg='#e0e0e0',
            wraplength=800,
            justify="center"
        )
        info_label.pack()

        # Animation canvas
        self.prevention_canvas = tk.Canvas(
            container,
            width=400,
            height=100,
            bg=self.frame_bg_color,
            highlightthickness=0
        )
        self.prevention_canvas.pack(pady=20)

        # Create initial file icons
        self.file_icons = []
        self.create_file_icons()

        # Button frame
        button_frame = tk.Frame(container, bg=self.frame_bg_color)
        button_frame.pack(pady=(0, 30))

        # Start Prevention Button
        self.start_prevention_btn = tk.Button(
            button_frame,
            text="Start Prevention",
            command=self.start_prevention,
            bg=self.button_color,
            fg=self.button_fg_color,
            font=('Helvetica', 14, 'bold'),
            relief=tk.FLAT,
            borderwidth=0,
            width=20,
            cursor="hand2"
        )
        self.start_prevention_btn.pack(pady=10)

        # Bind hover events
        self.start_prevention_btn.bind('<Enter>', lambda e: e.widget.config(bg='#0066CC'))
        self.start_prevention_btn.bind('<Leave>', lambda e: e.widget.config(bg=self.button_color))

        # Status frame
        status_frame = tk.Frame(container, bg=self.frame_bg_color)
        status_frame.pack(fill='x', pady=20)

        # Prevention Status Label
        self.prevention_status_label = tk.Label(
            status_frame,
            text="",
            font=('Helvetica', 12, 'bold'),
            bg=self.frame_bg_color,
            fg=self.status_fg_color
        )
        self.prevention_status_label.pack(pady=10)

        # File Paths Label
        self.file_paths_label = tk.Label(
            status_frame,
            text="",
            font=('Helvetica', 11),
            bg=self.frame_bg_color,
            fg=self.label_fg_color,
            wraplength=600,
            justify="left"
        )
        self.file_paths_label.pack(pady=10)

    def create_file_icons(self):
        # Clear existing icons
        self.prevention_canvas.delete("all")
        self.file_icons.clear()

        # Create file icons
        for i in range(5):
            x = 50 + i * 80
            y = 50
            icon = self.prevention_canvas.create_image(
                x, y,
                image=self.virus_icon
            )
            self.file_icons.append(icon)

    def animate_file_movement(self, moved_files):
        def move_files(step=0):
            if step < 20:  # Animation steps
                for icon in self.file_icons:
                    # Move up and right
                    self.prevention_canvas.move(icon, 2, -1)
                self.root.after(50, lambda: move_files(step + 1))
            else:
                # Replace with lock icons
                self.prevention_canvas.delete("all")
                for i in range(len(self.file_icons)):
                    x = 50 + i * 80
                    y = 30
                    self.prevention_canvas.create_image(
                        x, y,
                        image=self.lock_icon
                    )

        move_files()

    def start_prevention(self):
        try:
            prevention_result, moved_files = rotate_file_paths()
            if prevention_result:
                self.prevention_status_label.config(
                    text="Prevention successful: Files secured! 🛡️",
                    fg=self.status_fg_color
                )
                moved_files_text = "\n".join([f"✓ File moved: {source} ➜ {destination}"
                                            for source, destination in moved_files])
                self.file_paths_label.config(text=moved_files_text)
                self.animate_file_movement(moved_files)
                self.update_suspicious_files(moved_files)
            else:
                self.prevention_status_label.config(
                    text="Folder empty: No files found to move! ℹ️",
                    fg=self.status_fg_color
                )
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during prevention: {e}")

    def update_suspicious_files(self, moved_files):
        try:
            results_file_path = 'suspicious_files.txt'
            if os.path.exists(results_file_path):
                with open(results_file_path, 'r') as file:
                    suspicious_files = file.readlines()

                moved_file_names = {os.path.basename(file[0].strip())
                                  for file in moved_files}
                updated_suspicious_files = [
                    file for file in suspicious_files
                    if os.path.basename(file.strip()) not in moved_file_names
                ]

                with open(results_file_path, 'w') as file:
                    file.writelines(updated_suspicious_files)

                if updated_suspicious_files:
                    self.suspicious_files_label.config(
                        text="Suspicious Files Prevention done.")
                else:
                    self.suspicious_files_label.config(
                        text="No suspicious files detected.")
            else:
                self.suspicious_files_label.config(
                    text="No suspicious files detected.")
        except Exception as e:
            messagebox.showerror(
                "Error", f"An error occurred while updating suspicious files: {e}")

    def setup_report_tab(self):
        # Create container frame
        container = tk.Frame(
            self.report_frame,
            bg=self.frame_bg_color,
            padx=30,
            pady=20
        )
        container.pack(fill='both', expand=True)

        # Info Label with enhanced styling
        info_label = tk.Label(
            container,
            text="Generate concise summary or detailed report of detection and prevention activities",
            font=('Helvetica', 18, 'bold'),
            bg=self.frame_bg_color,
            fg='#e0e0e0',
            wraplength=800,
            justify="center"
        )
        info_label.pack(pady=(0, 30))

        # Report Options Frame with enhanced styling
        options_frame = tk.Frame(container, bg=self.frame_bg_color)
        options_frame.pack(pady=(0, 20))

        # Enhanced checkbox style
        checkbox_style = {
            'bg': self.frame_bg_color,
            'fg': '#e0e0e0',
            'selectcolor': '#0056A0',
            'activebackground': self.frame_bg_color,
            'activeforeground': '#e0e0e0',
            'font': ('Helvetica', 14),
            'bd': 0,
            'relief': tk.FLAT,
            'highlightthickness': 0
        }

        # Checkboxes with enhanced text
        self.include_detection = tk.BooleanVar(value=True)
        self.include_prevention = tk.BooleanVar(value=True)
        self.include_timestamps = tk.BooleanVar(value=True)
        self.detailed_report = tk.BooleanVar(value=False)

        # Create checkboxes
        self.detection_checkbox = tk.Checkbutton(
            options_frame,
            text="✓ Include Detection Results",
            variable=self.include_detection,
            **checkbox_style
        )
        self.detection_checkbox.pack(pady=8)

        self.prevention_checkbox = tk.Checkbutton(
            options_frame,
            text="✓ Include Prevention Actions",
            variable=self.include_prevention,
            **checkbox_style
        )
        self.prevention_checkbox.pack(pady=8)

        self.timestamps_checkbox = tk.Checkbutton(
            options_frame,
            text="✓ Include Timestamps",
            variable=self.include_timestamps,
            **checkbox_style
        )
        self.timestamps_checkbox.pack(pady=8)

        # Add separator
        separator = tk.Frame(options_frame, height=2, bg='#404040')
        separator.pack(fill='x', pady=15)

        # Detailed report checkbox
        self.detailed_checkbox = tk.Checkbutton(
            options_frame,
            text="⚠ Generate Detailed Report (May take longer to load)",
            variable=self.detailed_report,
            command=self.toggle_report_options,
            **checkbox_style
        )
        self.detailed_checkbox.pack(pady=8)

        # Button frame
        button_frame = tk.Frame(container, bg=self.frame_bg_color)
        button_frame.pack(pady=(20, 30))

        # Generate Report Button
        self.generate_report_btn = tk.Button(
            button_frame,
            text="Generate Report",
            command=self.generate_report,
            bg=self.button_color,
            fg=self.button_fg_color,
            font=('Helvetica', 14, 'bold'),
            relief=tk.FLAT,
            borderwidth=0,
            width=20,
            cursor="hand2"
        )
        self.generate_report_btn.pack(pady=10)

        # Bind hover events
        self.generate_report_btn.bind('<Enter>', lambda e: e.widget.config(bg='#0066CC'))
        self.generate_report_btn.bind('<Leave>', lambda e: e.widget.config(bg=self.button_color))

        # Loading animation canvas (hidden initially)
        self.report_loading_canvas = tk.Canvas(
            container,
            width=100,  # Increased size to match detection animation
            height=100,  # Increased size to match detection animation
            bg=self.frame_bg_color,
            highlightthickness=0
        )
        self.report_loading_canvas.pack_forget()

        # Status frame
        status_frame = tk.Frame(container, bg=self.frame_bg_color)
        status_frame.pack(fill='x', pady=20)

        # Report Status Label
        self.report_status_label = tk.Label(
            status_frame,
            text="",
            font=('Helvetica', 12, 'bold'),
            bg=self.frame_bg_color,
            fg=self.status_fg_color
        )
        self.report_status_label.pack(pady=10)

        # Report File Paths Label
        self.report_file_paths_label = tk.Label(
            status_frame,
            text="",
            font=('Helvetica', 11),
            bg=self.frame_bg_color,
            fg=self.label_fg_color,
            wraplength=600,
            justify="left"
        )
        self.report_file_paths_label.pack(pady=10)

    def toggle_report_options(self):
        # Enable/disable other checkboxes based on detailed report selection
        state = 'disabled' if self.detailed_report.get() else 'normal'
        self.detection_checkbox.config(state=state)
        self.prevention_checkbox.config(state=state)
        self.timestamps_checkbox.config(state=state)

    def create_report_loading_animation(self):
        # Use the same animation style as detection tab
        self.report_loading_canvas.delete("all")
        
        # Animation parameters
        center_x = 50
        center_y = 50
        max_radius = 35
        num_circles = 8
        angle = int(time.time() * 300) % 360  # Faster rotation
        
        for i in range(num_circles):
            # Calculate position for each circle
            circle_angle = angle + (i * (360 / num_circles))
            radius = max_radius
            size = 8  # Size of each circle
            
            # Calculate position with sine wave effect
            x = center_x + radius * math.cos(math.radians(circle_angle))
            y = center_y + radius * math.sin(math.radians(circle_angle))
            
            # Color gradient from blue to white
            color_intensity = (i / num_circles)
            color = self.interpolate_color('#0056A0', '#FFFFFF', color_intensity)
            
            # Draw circle with fade effect
            self.report_loading_canvas.create_oval(
                x - size/2, y - size/2,
                x + size/2, y + size/2,
                fill=color,
                outline=color
            )
        
        self.root.after(20, self.create_report_loading_animation)

    def interpolate_color(self, color1, color2, factor):
        # Convert hex colors to RGB
        r1 = int(color1[1:3], 16)
        g1 = int(color1[3:5], 16)
        b1 = int(color1[5:7], 16)
        
        r2 = int(color2[1:3], 16)
        g2 = int(color2[3:5], 16)
        b2 = int(color2[5:7], 16)
        
        # Interpolate
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        
        # Convert back to hex
        return f'#{r:02x}{g:02x}{b:02x}'

    def create_loading_animation(self):
        # Create loading animation with multiple circles
        self.loading_canvas.delete("all")
        
        # Animation parameters
        center_x = 50
        center_y = 50
        max_radius = 35
        num_circles = 8
        angle = int(time.time() * 300) % 360  # Faster rotation
        
        for i in range(num_circles):
            # Calculate position for each circle
            circle_angle = angle + (i * (360 / num_circles))
            radius = max_radius
            size = 8  # Size of each circle
            
            # Calculate position with sine wave effect
            x = center_x + radius * math.cos(math.radians(circle_angle))
            y = center_y + radius * math.sin(math.radians(circle_angle))
            
            # Color gradient from blue to white
            color_intensity = (i / num_circles)
            color = self.interpolate_color('#0056A0', '#FFFFFF', color_intensity)
            
            # Draw circle with fade effect
            self.loading_canvas.create_oval(
                x - size/2, y - size/2,
                x + size/2, y + size/2,
                fill=color,
                outline=color
            )
        
        self.root.after(20, self.create_loading_animation)  # Faster update rate

    def show_detection_results(self, results, severity, severity_color):
        # Create custom popup window
        popup = tk.Toplevel(self.root)
        popup.title("Detection Results")
        popup.geometry("500x600")  # Adjust size as needed
        popup.configure(bg=self.frame_bg_color)
        
        # Center the popup on screen
        window_width = 500
        window_height = 600
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        popup.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Make popup modal
        popup.transient(self.root)
        popup.grab_set()
        
        # Title with enhanced styling
        title = tk.Label(
            popup,
            text="Ransomware Detection Results",
            font=('Helvetica', 20, 'bold'),
            fg='white',
            bg=self.frame_bg_color
        )
        title.pack(pady=25)

        # Severity Level Label
        severity_label = tk.Label(
            popup,
            text=f"Severity Level: {severity}",
            font=('Helvetica', 16, 'bold'),
            fg=severity_color,
            bg=self.frame_bg_color
        )
        severity_label.pack(pady=10)

        # Create frame for results
        results_frame = tk.Frame(popup, bg=self.frame_bg_color)
        results_frame.pack(fill='both', expand=True, padx=30, pady=(0, 20))
        
        # Add results with icons
        for component, detected in results.items():
            result_frame = tk.Frame(results_frame, bg=self.frame_bg_color)
            result_frame.pack(fill='x', pady=8)
            
            # Status icon (green checkmark or red X)
            status_label = tk.Label(
                result_frame,
                text="❌" if detected else "✓",
                font=('Helvetica', 16),
                fg='red' if detected else '#00ff00',
                bg=self.frame_bg_color
            )
            status_label.pack(side='left', padx=(0, 15))
            
            # Component name
            name_label = tk.Label(
                result_frame,
                text=component,
                font=('Helvetica', 14, 'bold'),
                fg='white',
                bg=self.frame_bg_color
            )
            name_label.pack(side='left')
            
            # Status text
            status_text = tk.Label(
                result_frame,
                text="Ransomware Detected" if detected else "No Ransomware Detected",
                font=('Helvetica', 13),
                fg='red' if detected else '#00ff00',
                bg=self.frame_bg_color
            )
            status_text.pack(side='right')
        
        # Bottom frame for OK button
        bottom_frame = tk.Frame(popup, bg=self.frame_bg_color)
        bottom_frame.pack(side='bottom', fill='x', pady=25)
        
        # OK Button with enhanced styling
        ok_button = tk.Button(
            bottom_frame,
            text="OK",
            command=popup.destroy,
            bg=self.button_color,
            fg='white',
            font=('Helvetica', 13, 'bold'),
            relief=tk.FLAT,
            borderwidth=0,
            width=15,
            height=2,
            cursor="hand2"
        )
        ok_button.pack(pady=10)
        
        # Bind hover events for OK button
        ok_button.bind('<Enter>', lambda e: e.widget.config(bg='#0066CC'))
        ok_button.bind('<Leave>', lambda e: e.widget.config(bg=self.button_color))

    def start_detection(self):
        try:
            # Show loading animation
            self.start_detection_btn.config(state='disabled')
            self.loading_canvas.pack(pady=10)
            self.create_loading_animation()
            
            # Clear previous plot
            for widget in self.plot_frame.winfo_children():
                widget.destroy()

            results = {}
            
            def run_detection():
                # Run detection processes and store results
                results['Behavioral'] = subprocess.Popen(["python", "detection/behavioral_analysis.py"]).wait() == 1
                results['File System'] = subprocess.Popen(["python", "detection/file_system_monitoring.py"]).wait() == 1
                results['Net Traffic'] = subprocess.Popen(["python", "detection/network_traffic_analysis.py"]).wait() == 1
                results['Registry'] = subprocess.Popen(["python", "detection/registry_monitoring.py"]).wait() == 1
                results['Process'] = subprocess.Popen(["python", "detection/process_monitoring.py"]).wait() == 1
                results['API'] = subprocess.Popen(["python", "detection/api_calls_analysis.py"]).wait() == 1
                results['Static'] = subprocess.Popen(["python", "detection/static_analysis.py"]).wait() == 1

                # Calculate severity
                detections_count = sum(results.values())
                if detections_count >= 5:
                    severity = "Severe"
                    severity_color = 'red'
                elif 2 <= detections_count <= 4:
                    severity = "Mild"
                    severity_color = 'orange'
                elif 1 <= detections_count <= 2:
                    severity = "Normal"
                    severity_color = 'white'
                else:
                    severity = "No Ransomware"
                    severity_color = 'white'

                # Generate detailed report
                os.makedirs('reports', exist_ok=True)
                report_path = 'reports/detection_and-prevention_report.txt'
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write("=== Detailed Ransomware Detection and Prevention Report ===\n\n")
                    f.write(f"Report Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    f.write("Detection Results:\n")
                    f.write(f"Severity Level: {severity}\n\n")
                    
                    for component, detected in results.items():
                        f.write(f"{component} Analysis:\n")
                        f.write(f"Status: {'Ransomware Detected' if detected else 'No Ransomware Detected'}\n")
                        f.write(f"Result: {'❌ Failed' if detected else '✓ Passed'}\n\n")
                    
                    f.write("Suspicious Files:\n")
                    try:
                        with open('suspicious_files.txt', 'r', encoding='utf-8') as sf:
                            suspicious_files = sf.readlines()
                            if suspicious_files:
                                for file in suspicious_files:
                                    f.write(f"- {file.strip()}\n")
                            else:
                                f.write("No suspicious files detected\n")
                    except FileNotFoundError:
                        f.write("No suspicious files detected\n")
                    f.write("\n")
                    
                    f.write("Prevention Status:\n")
                    f.write("- Moving Target Defense: Active\n")
                    f.write("- System Monitoring: Enabled\n")
                    f.write("- Critical Files: Protected\n\n")
                    
                    try:
                        with open('prevention/mtd_routes.txt', 'r', encoding='utf-8') as routes:
                            f.write("Recent MTD Actions:\n")
                            recent_routes = routes.readlines()
                            if recent_routes:
                                for route in recent_routes[-5:]:
                                    route = route.replace('→', '->')
                                    f.write(f"- {route.strip()}\n")
                            else:
                                f.write("No recent MTD actions recorded\n")
                    except FileNotFoundError:
                        f.write("No MTD actions recorded\n")
                    f.write("\n")
                    
                    f.write("System Status: ")
                    if severity == "Severe":
                        f.write("CRITICAL - Immediate action required\n")
                    elif severity == "Mild":
                        f.write("WARNING - Monitor closely\n")
                    else:
                        f.write("SECURE - No immediate threats detected\n")

                # Update UI in main thread
                self.root.after(0, lambda: self.update_detection_ui(results, severity, severity_color))
            
            # Run detection in separate thread
            threading.Thread(target=run_detection, daemon=True).start()

        except Exception as e:
            self.loading_canvas.pack_forget()
            self.start_detection_btn.config(state='normal')
            messagebox.showerror("Error", f"An error occurred: {e}")

    def update_detection_ui(self, results, severity, severity_color):
        # Hide loading animation
        self.loading_canvas.pack_forget()
        self.start_detection_btn.config(state='normal')
        
        # Update severity label
        self.severity_label.config(text=f"Severity Level: {severity}", fg=severity_color)
        
        # Clear suspicious files display
        self.suspicious_files_label.config(text="")  # Clear previous suspicious files

        # Show results popup with severity
        self.show_detection_results(results, severity, severity_color)
        
        # Plot results
        self.plot_results(results)

    def display_suspicious_files(self):
        try:
            results_file_path = 'suspicious_files.txt'
            if os.path.exists(results_file_path):
                with open(results_file_path, 'r') as file:
                    suspicious_files = file.readlines()
                
                if suspicious_files:
                    file_details = "".join([f"{file.strip()}\n" for file in suspicious_files])
                    recently_detected = "Recently detected files history"
                    self.recently_detected_label.config(text=recently_detected)
                    self.suspicious_files_label.config(text=file_details)
                else:
                    self.suspicious_files_label.config(text="No suspicious files detected.")
            else:
                self.suspicious_files_label.config(text="No suspicious files detected.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while reading the suspicious files: {e}")

    def plot_results(self, results):
        # Create figure and axis with adjusted size
        fig, ax = plt.subplots(figsize=(8, 4), facecolor=self.frame_bg_color)  # Adjusted size
        ax.set_facecolor(self.frame_bg_color)

        # Plot data
        components = list(results.keys())
        detection_status = [1 if detected else 0 for detected in results.values()]
        bars = ax.bar(components, detection_status,
                     color=['red' if status else 'green' for status in detection_status])

        # Customize plot
        ax.set_xlabel('Detection Components', color=self.label_fg_color)
        ax.set_ylabel('Ransomware Detected (1) / Not Detected (0)',
                     color=self.label_fg_color)
        ax.set_title('Ransomware Detection Results', color=self.label_fg_color)
        plt.xticks(rotation=45, ha='right', color=self.label_fg_color)
        plt.yticks(color=self.label_fg_color)

        # Add edge color to bars
        for bar in bars:
            bar.set_edgecolor('black')
        
        plt.tight_layout(pad=3.0)  # Adjust padding

        # Clear previous widgets in the plot frame to avoid stacking
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        
        # Embed plot in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        
        # Pack the canvas widget
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def generate_report(self):
        # Disable button and show loading
        self.generate_report_btn.config(state='disabled')
        self.report_loading_canvas.pack(pady=10)
        self.create_report_loading_animation()
        
        def generate():
            try:
                # Create reports directory if it doesn't exist
                os.makedirs('reports', exist_ok=True)
                
                if self.detailed_report.get():
                    # Use existing detailed report
                    report_path = 'reports/detection_and-prevention_report.txt'
                    if not os.path.exists(report_path):
                        raise FileNotFoundError("Detailed report file not found. Please run a detection first.")
                else:
                    # Generate summary report
                    report_path = 'reports/summary_report.txt'
                    
                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write("=== Ransomware Detection and Prevention Summary ===\n\n")
                        
                        if self.include_timestamps.get():
                            f.write(f"Report Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        
                        if self.include_detection.get():
                            f.write("Detection Summary:\n")
                            f.write("- Last scan completed successfully\n")
                            
                            try:
                                with open('suspicious_files.txt', 'r', encoding='utf-8') as sf:
                                    suspicious_files = sf.readlines()
                                    if suspicious_files:
                                        f.write("\nDetected Suspicious Files:\n")
                                        for file in suspicious_files:
                                            f.write(f"- {file.strip()} -> routed to suspicious_mtd\n")
                                    else:
                                        f.write("- No suspicious files detected\n")
                            except FileNotFoundError:
                                f.write("- No suspicious files detected\n")
                            f.write("\n")
                        
                        if self.include_prevention.get():
                            f.write("Prevention Summary:\n")
                            f.write("- Moving Target Defense active\n")
                            f.write("- Critical files protected\n")
                            f.write("- System monitoring enabled\n")
                            
                            try:
                                with open('prevention/mtd_routes.txt', 'r', encoding='utf-8') as routes:
                                    recent_routes = routes.readlines()
                                    if recent_routes:
                                        f.write("\nRecent MTD Actions:\n")
                                        for route in recent_routes[-5:]:
                                            route = route.replace('→', '->')
                                            f.write(f"- {route.strip()}\n")
                            except FileNotFoundError:
                                pass
                            f.write("\n")
                        
                        f.write("Status: System Protected\n")

                # Show text report
                self.show_text_report(report_path)

                # Update UI in main thread
                self.root.after(0, self.report_generation_complete, report_path)
            
            except Exception as e:
                self.root.after(0, self.report_generation_failed, str(e))
        
        # Run report generation in separate thread
        threading.Thread(target=generate, daemon=True).start()

    def report_generation_complete(self, report_path):
        # Hide loading animation and enable button
        self.report_loading_canvas.pack_forget()
        self.generate_report_btn.config(state='normal')
        
        # Update status
        self.report_status_label.config(
            text="Report Generated Successfully",
            fg=self.status_fg_color
        )
        self.report_file_paths_label.config(
            text=f"Report saved to: {report_path}",
            fg=self.label_fg_color
        )
        
        # Show success message
        messagebox.showinfo(
            "Success",
            f"Concise summary report generated successfully!\nLocation: {report_path}"
        )

    def report_generation_failed(self, error):
        # Hide loading animation and enable button
        self.report_loading_canvas.pack_forget()
        self.generate_report_btn.config(state='normal')
        
        # Update status
        self.report_status_label.config(
            text="Report Generation Failed",
            fg=self.error_fg_color
        )
        
        # Show error message
        messagebox.showerror("Error", f"Failed to generate report: {error}")

    def show_text_report(self, text_path):
        try:
            # Verify the text file exists
            if not os.path.exists(text_path):
                raise FileNotFoundError(f"Report file not found: {text_path}")

            # Create popup window for text report
            popup = tk.Toplevel(self.root)
            popup.title("Report Viewer")
            popup.geometry("800x600")
            popup.configure(bg=self.frame_bg_color)
            
            # Make the window modal
            popup.transient(self.root)
            popup.grab_set()
            
            # Center the popup
            window_width = 800
            window_height = 600
            screen_width = popup.winfo_screenwidth()
            screen_height = popup.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            popup.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Create main container with padding
            container = tk.Frame(popup, bg=self.frame_bg_color)
            container.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Add title
            title = tk.Label(
                container,
                text="Ransomware Detection and Prevention Report",
                font=('Helvetica', 16, 'bold'),
                bg=self.frame_bg_color,
                fg='white'
            )
            title.pack(pady=(0, 20))
            
            # Create text widget with scrollbar
            text_frame = tk.Frame(container, bg=self.frame_bg_color)
            text_frame.pack(fill='both', expand=True)
            
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side='right', fill='y')
            
            text_widget = tk.Text(
                text_frame,
                wrap=tk.WORD,
                bg=self.frame_bg_color,
                fg='white',
                font=('Helvetica', 12),
                padx=10,
                pady=10,
                yscrollcommand=scrollbar.set
            )
            text_widget.pack(side='left', fill='both', expand=True)
            
            scrollbar.config(command=text_widget.yview)
            
            # Read and display the report
            with open(text_path, 'r', encoding='utf-8') as f:
                text_widget.insert('1.0', f.read())
            
            text_widget.config(state='disabled')  # Make read-only
            
            # Button frame
            button_frame = tk.Frame(container, bg=self.frame_bg_color)
            button_frame.pack(pady=(20, 0))
            
            # Save as PDF button
            save_pdf_button = tk.Button(
                button_frame,
                text="Save as PDF",
                command=lambda: self.save_as_pdf(text_path),
                bg='#ff3333',  # Red background
                fg='white',
                font=('Helvetica', 12, 'bold'),
                relief=tk.FLAT,
                borderwidth=0,
                width=15,
                height=2,
                cursor="hand2"
            )
            save_pdf_button.pack(side='left', padx=5)

            # Close button
            close_button = tk.Button(
                button_frame,
                text="Close",
                command=popup.destroy,
                bg=self.button_color,
                fg='white',
                font=('Helvetica', 12, 'bold'),
                relief=tk.FLAT,
                borderwidth=0,
                width=15,
                height=2,
                cursor="hand2"
            )
            close_button.pack(side='left', padx=5)
            
            # Bind hover events for buttons
            save_pdf_button.bind('<Enter>', lambda e: e.widget.config(bg='#cc0000'))
            save_pdf_button.bind('<Leave>', lambda e: e.widget.config(bg='#ff3333'))
            close_button.bind('<Enter>', lambda e: e.widget.config(bg='#0066CC'))
            close_button.bind('<Leave>', lambda e: e.widget.config(bg=self.button_color))

        except Exception as e:
            messagebox.showerror("Error", f"Could not display report: {str(e)}")
            popup.destroy() if 'popup' in locals() else None

    def save_as_pdf(self, text_path):
        try:
            # Specify the directory to save the PDF
            pdf_directory = r"C:\Users\sawan\Downloads"
            pdf_path = os.path.join(pdf_directory, os.path.basename(text_path).replace('.txt', '.pdf'))
            
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # Register a Unicode font
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
                font_name = 'DejaVuSans'
            except:
                font_name = 'Helvetica'
            
            doc = SimpleDocTemplate(pdf_path, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Create custom styles with Unicode font
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#0056A0'),
                fontName=font_name
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=18,
                spaceAfter=12,
                textColor=colors.HexColor('#333333'),
                fontName=font_name
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=8,
                textColor=colors.HexColor('#000000'),
                fontName=font_name
            )
            
            # Read text content and convert to PDF elements
            with open(text_path, 'r', encoding='utf-8') as f:
                content = f.read().split('\n')
            
            elements = []
            
            # Process each line and apply appropriate styling
            for line in content:
                if line.startswith('==='):
                    elements.append(Paragraph(line.strip('=').strip(), title_style))
                elif line.endswith(':'):
                    elements.append(Paragraph(line, heading_style))
                elif line.strip():
                    # Replace any remaining special characters
                    line = line.replace('→', '->')
                    elements.append(Paragraph(line, normal_style))
                else:
                    elements.append(Spacer(1, 12))
            
            # Generate PDF
            doc.build(elements)
            
            # Open the PDF file with the default viewer
            subprocess.Popen([pdf_path], shell=True)

            messagebox.showinfo(
                "Success",
                f"PDF saved successfully!\nLocation: {pdf_path}"
            )
            
        except ImportError:
            messagebox.showerror(
                "Error",
                "ReportLab not installed. Please install it using:\npip install reportlab"
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not generate PDF: {str(e)}"
            )

    def setup_exit_tab(self):
        # Create container frame with padding
        container = tk.Frame(
            self.exit_frame,
            bg=self.frame_bg_color,
            padx=30,
            pady=20
        )
        container.pack(fill='both', expand=True)

        # Warning Label
        warning_label = tk.Label(
            container,
            text="Are you sure you want to exit?",
            font=('Helvetica', 18, 'bold'),
            bg=self.frame_bg_color,
            fg='#e0e0e0',
            wraplength=800,
            justify="center"
        )
        warning_label.pack(pady=(100, 40))

        # Button frame
        button_frame = tk.Frame(container, bg=self.frame_bg_color)
        button_frame.pack(pady=20)

        # Exit Button
        self.exit_button = tk.Button(
            button_frame,
            text="Exit Application",
            command=self.exit_app,
            bg='#ff3333',
            fg='white',
            font=('Helvetica', 16, 'bold'),
            relief=tk.FLAT,
            borderwidth=0,
            width=20,
            height=2,
            cursor="hand2"
        )
        self.exit_button.pack(pady=20)

        # Bind hover events
        self.exit_button.bind('<Enter>', lambda e: e.widget.config(bg='#cc0000'))
        self.exit_button.bind('<Leave>', lambda e: e.widget.config(bg='#ff3333'))

    def exit_app(self):
        self.root.quit()

def send_email_with_attachment(to_email, subject, body, attachment_path):
    try:
        smtp_server = 'smtp.freesmtpservers.com'  # Use Gmail's SMTP server
        smtp_port = 25  # Use port 587 for TLS
        sender_email = 'codewithvacky@gmail.com'  # Your email
        sender_password = 'vackyhub@321'  # Use App Password if 2FA is enabled

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
            msg.attach(part)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)  # Log in to your email account
            server.send_message(msg)  # Send the email

        messagebox.showinfo("Success", "Email sent successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to send email: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RansomwareApp(root)
    root.mainloop()