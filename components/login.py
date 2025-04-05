from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QLineEdit, QFrame, QMessageBox, QApplication,
                           QGraphicsDropShadowEffect, QProgressDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QColor
from config.firebase_config import firebase_auth
from .signup import SignupWindow
from utils.firebase_auth import FirebaseAuth
from .admin_update import AdminUpdateWindow  # Import the new admin update window

class LoginWindow(QMainWindow):
    # Define signals for communication
    user_authenticated = pyqtSignal(str, str)  # email, role
    login_cancelled = pyqtSignal()

    def __init__(self, role="Admin"):
        super().__init__()
        self.role = role
        self.signup_window = None
        self.admin_update_window = None  # Add reference for admin update window
        self.firebase_auth = FirebaseAuth()
        # Initialize input fields
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(f"{self.role.title()} Login")
        self.setFixedSize(1200, 1250)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(100, 60, 100, 60)
        
        # Create logo layout
        logo_frame = QFrame()
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setSpacing(40)  # Space between logos
        logo_layout.setContentsMargins(0, 0, 0, 30)  # Add bottom margin
        
        # Load and add logos
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
        
        layout.addWidget(logo_frame)
        
        # Main content container
        content_container = QFrame()
        content_container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 20px;
            }
        """)
        content_layout = QVBoxLayout(content_container)
        content_layout.setSpacing(30)
        content_layout.setContentsMargins(50, 40, 50, 40)

        # Header with role icon
        role_container = QFrame()
        role_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #1976D2, stop:1 #2196F3);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        role_layout = QVBoxLayout(role_container)
        role_layout.setSpacing(15)

        # Role icon and welcome text
        role_icon = "👤" if self.role == 'student' else "👨‍🏫" if self.role == 'faculty' else "⚙️"
        icon_label = QLabel(role_icon)
        icon_label.setFont(QFont('Helvetica', 32))
        icon_label.setStyleSheet("color: white;")
        icon_label.setAlignment(Qt.AlignCenter)
        role_layout.addWidget(icon_label)

        welcome_text = QLabel(f"Welcome Back, {self.role.title()}")
        welcome_text.setFont(QFont('Helvetica', 18, QFont.Bold))
        welcome_text.setStyleSheet("color: white;")
        welcome_text.setAlignment(Qt.AlignCenter)
        role_layout.addWidget(welcome_text)

        content_layout.addWidget(role_container)

        # Login form container
        form_container = QFrame()
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(20)

        # Input fields
        for label_text, input_field, placeholder in [
            ("Email Address", self.email_input, "Enter your email"),
            ("Password", self.password_input, "Enter your password")
        ]:
            # Label
            label = QLabel(label_text)
            label.setFont(QFont('Helvetica', 14))  # Increased from 12
            label.setStyleSheet("color: #666666;")
            form_layout.addWidget(label)

            # Input field
            input_field.setFixedHeight(55)  # Increased from 50
            input_field.setPlaceholderText(placeholder)
            input_field.setFont(QFont('Helvetica', 13))  # Increased from 14
            input_field.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 10px 15px;
                    background: white;
                }
                QLineEdit:focus {
                    border: 2px solid #2196F3;
                }
            """)
            form_layout.addWidget(input_field)

        content_layout.addWidget(form_container)

        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.setFixedSize(300, 60)
        self.login_btn.setFont(QFont('Helvetica', 14, QFont.Bold))
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.login_btn.clicked.connect(self.authenticate)
        content_layout.addWidget(self.login_btn, alignment=Qt.AlignCenter)

        # Add content container to main layout
        layout.addWidget(content_container)

        # Create account or update admin link
        if self.role.lower() == 'admin':
            signup_link = QLabel("Need to update admin credentials? <a href='#'>Update now</a>")
        else:
            signup_link = QLabel("Don't have an account? <a href='#'>Sign up now</a>")
            
        signup_link.setFont(QFont('Helvetica', 11))
        signup_link.setStyleSheet("color: #666666;")
        signup_link.setAlignment(Qt.AlignCenter)
        signup_link.setOpenExternalLinks(False)
        if self.role.lower() == 'admin':
            signup_link.linkActivated.connect(self.show_admin_update)
        else:
            signup_link.linkActivated.connect(self.show_signup)
        layout.addWidget(signup_link)

        # Back button
        back_btn = QPushButton("← Back")
        back_btn.setFont(QFont('Helvetica', 12))
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                color: #666666;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        back_btn.clicked.connect(self.handle_back)
        layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        # Add stretches for vertical centering
        layout.insertStretch(0)
        layout.addStretch()

        self.center_window()

    def center_window(self):
        frame = self.frameGeometry()
        center = QApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(center)
        self.move(frame.topLeft())

    def authenticate(self):
        """Authenticate the user using Firebase"""
        email = self.email_input.text()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both email and password.")
            return
        
        # Show progress dialog during authentication
        progress = QProgressDialog("Logging in...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Please Wait")
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        
        # Try to sign in with Firebase
        result = self.firebase_auth.sign_in(email, password)
        
        # Close progress dialog
        progress.close()
        
        if result["success"]:
            # Store remember me preference if selected
            if hasattr(self, 'remember_checkbox') and self.remember_checkbox.isChecked():
                # In a real app, you would securely store credentials
                # For this demo, we'll just keep the user logged in via the auth token
                pass
                
            # Emit authenticated signal with email and role
            self.user_authenticated.emit(email, result["role"])
            self.hide()
        else:
            QMessageBox.warning(
                self,
                "Login Error",
                result["message"]
            )

    def handle_back(self):
        self.login_cancelled.emit()
        self.close()

    def show_signup(self):
        """Show signup window"""
        self.signup_window = SignupWindow(self.role)
        self.signup_window.signup_successful.connect(self.on_signup_success)
        self.signup_window.signup_cancelled.connect(self.on_signup_cancelled)
        self.signup_window.show()
        self.hide()
    
    def show_admin_update(self):
        """Show admin update window"""
        self.admin_update_window = AdminUpdateWindow()
        self.admin_update_window.update_successful.connect(self.on_admin_update_success)
        self.admin_update_window.update_cancelled.connect(self.on_admin_update_cancelled)
        self.admin_update_window.show()
        self.hide()
    
    def on_signup_success(self, email, role):
        """Handle successful signup"""
        # Pre-fill the email field
        self.email_input.setText(email)
        self.show()
        
        # Show success message
        QMessageBox.information(
            self,
            "Account Created",
            f"Your {role} account has been created successfully!\n\nPlease login with your new credentials."
        )
    
    def on_signup_cancelled(self):
        """Handle signup cancellation"""
        self.show()
    
    def on_admin_update_success(self, email):
        """Handle successful admin credentials update"""
        # Pre-fill the email field
        self.email_input.setText(email)
        self.show()
        
        # Show success message
        QMessageBox.information(
            self,
            "Admin Credentials Updated",
            "Your admin credentials have been updated successfully!\n\nPlease login with your new credentials."
        )
    
    def on_admin_update_cancelled(self):
        """Handle admin update cancellation"""
        self.show()
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.login_cancelled.emit()
        event.accept()
