from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QLineEdit, QFormLayout, QFrame,
                           QMessageBox, QCheckBox, QApplication, QProgressDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap

# Import Firebase authentication
from utils.firebase_auth import FirebaseAuth

class SignupWindow(QMainWindow):
    """SignUp window for user registration"""
    
    # Signals for communicating with other windows
    signup_successful = pyqtSignal(str, str)  # Emits email and role
    signup_cancelled = pyqtSignal()
    
    def __init__(self, role="student"):
        super().__init__()
        self.role = role
        self.firebase_auth = FirebaseAuth()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(f"{self.role.title()} Signup")
        self.setFixedSize(1200, 1300)  # Match login window size
        
        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(100, 60, 100, 60)  # Adjusted margins
        main_layout.setSpacing(30)  # Reduced spacing
        
        # Create logo layout - same as login.py
        logo_frame = QFrame()
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setSpacing(40)  # Space between logos
        logo_layout.setContentsMargins(0, 0, 0, 30)  # Add bottom margin
        
        # Load and add logos - same as login.py
        logo_files = ["pillai_flower.png", "pillai_name.png", "pillai_naac.png"]
        logo_sizes = [(150, 120), (650, 150), (150, 120)]  # Width, height for each logo
        
        try:
            for logo_file, (width, height) in zip(logo_files, logo_sizes):
                logo_label = QLabel()
                pixmap = QPixmap(f"drawable/{logo_file}")
                scaled_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignCenter)
                logo_layout.addWidget(logo_label)
        except Exception as e:
            print(f"Could not load logos: {e}")
        
        main_layout.addWidget(logo_frame)
        
        # Header section with blue gradient - same as login.py
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #2196F3, stop:1 #1976D2);
                border-radius: 15px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(10)  # Reduced spacing
        
        # Title label
        title_label = QLabel(f"{self.role.title()} Signup")
        title_label.setFont(QFont('Helvetica', 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: white;")
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle = QLabel("Please fill in your details to create a new account")
        subtitle.setFont(QFont('Helvetica', 11))
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)
        
        main_layout.addWidget(header_frame)
        
        # Signup form - Use QFormLayout like login.py
        signup_frame = QFrame()
        signup_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 10px;
                margin-top: 20px;
            }}
        """)
        form_layout = QFormLayout(signup_frame)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(10)
        
        # Email field - match login.py styling but with larger font
        email_label = QLabel("Email:")
        email_label.setFont(QFont('Helvetica', 14))  # Increased font size
        form_layout.addRow(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setMinimumHeight(70)  # Increased height
        self.email_input.setFont(QFont('Helvetica', 24))  # Increased font size
        self.email_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px 15px;
                background-color: white;
                font-size: 20px;  /* Increased font size */
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        form_layout.addRow(self.email_input)
        
        # New Password field - match login.py styling but with larger font
        password_label = QLabel("New Password:")
        password_label.setFont(QFont('Helvetica', 14))  # Increased font size
        form_layout.addRow(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Create a password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(60)  # Increased height
        self.password_input.setFont(QFont('Helvetica', 16))  # Increased font size
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px 15px;
                background-color: white;
                font-size: 18px;  /* Increased font size */
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        form_layout.addRow(self.password_input)
        
        # Confirm Password field - match login.py styling but with larger font
        confirm_label = QLabel("Confirm Password:")
        confirm_label.setFont(QFont('Helvetica', 14))  # Increased font size
        form_layout.addRow(confirm_label)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm your password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setMinimumHeight(60)  # Increased height
        self.confirm_password_input.setFont(QFont('Helvetica', 16))  # Increased font size
        self.confirm_password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px 15px;
                background-color: white;
                font-size: 18px;  /* Increased font size */
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        form_layout.addRow(self.confirm_password_input)
        
        # Removed terms checkbox
        
        main_layout.addWidget(signup_frame)
        
        # Signup button - blue to match login.py
        signup_btn = QPushButton("Sign Up")
        signup_btn.setMinimumHeight(70)
        signup_btn.setFont(QFont('Helvetica', 14, QFont.Bold))
        signup_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        signup_btn.clicked.connect(self.create_account)
        main_layout.addWidget(signup_btn)
        
        # Back to login link - match login.py style
        back_link = QLabel("Already have an account? <a href='#' style='color:#2196F3;'>Log In</a>")
        back_link.setFont(QFont('Helvetica', 12))
        back_link.setStyleSheet("color: #666666; margin-top: 10px;")
        back_link.setAlignment(Qt.AlignCenter)
        back_link.setOpenExternalLinks(False)
        back_link.linkActivated.connect(self.back_to_login)
        main_layout.addWidget(back_link)
        
        # Add stretches for better vertical distribution
        main_layout.addStretch(1)
        
        # Center the window
        self.center_window()
    
    def center_window(self):
        """Center the window on screen"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def darken_color(self, color_hex):
        """Create a darker version of the given hex color"""
        # Remove # if present
        color_hex = color_hex.lstrip('#')
        
        # Convert to RGB
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)
        
        # Darken (multiply by 0.8)
        r = max(0, int(r * 0.8))
        g = max(0, int(g * 0.8))
        b = max(0, int(b * 0.8))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
        
    def create_account(self):
        """Handle signup form submission with Firebase authentication"""
        # Validate form fields
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        # Basic validation
        if not email or '@' not in email:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid email address.")
            return
            
        if not password:
            QMessageBox.warning(self, "Validation Error", "Please create a password.")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "Validation Error", "Password must be at least 6 characters long.")
            return
            
        if password != confirm_password:
            QMessageBox.warning(self, "Validation Error", "Passwords do not match.")
            return
        
        # Show progress dialog during authentication
        progress = QProgressDialog("Creating your account...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Please Wait")
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        
        # Try to create Firebase account
        result = self.firebase_auth.sign_up(email, password, self.role)
        
        # Close progress dialog
        progress.close()
        
        if result["success"]:
            # Show success message (customize based on whether it's online/offline)
            if result.get("offline"):
                QMessageBox.information(
                    self, 
                    "Account Created (Offline Mode)",
                    f"Your {self.role} account has been created locally in offline mode.\n\n"
                    f"You can now log in with your email and password, but your account "
                    f"will only be available on this device."
                )
            else:
                QMessageBox.information(
                    self, 
                    "Account Created",
                    f"Your {self.role} account has been created successfully!\n\n"
                    f"You can now log in with your email and password."
                )
            
            # Emit signal with email and role
            self.signup_successful.emit(email, self.role)
            
            # Close the window
            self.close()
        else:
            # Show error message
            QMessageBox.warning(self, "Account Creation Failed", result["message"])
        
    def back_to_login(self):
        """Go back to login screen"""
        self.signup_cancelled.emit()
        self.close()
        
    def closeEvent(self, event):
        """Handle window close event"""
        # If closed without completing signup, emit cancelled signal
        self.signup_cancelled.emit()
        event.accept()
