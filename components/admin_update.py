from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QLineEdit, QFormLayout, QFrame,
                           QMessageBox, QApplication, QProgressDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap

# Import Firebase authentication
from utils.firebase_auth import FirebaseAuth

class AdminUpdateWindow(QMainWindow):
    """Admin credentials update window"""
    
    # Signals for communicating with other windows
    update_successful = pyqtSignal(str)  # Emits email
    update_cancelled = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.firebase_auth = FirebaseAuth()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Admin Credentials Update")
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
        
        main_layout.addWidget(logo_frame)
        
        # Header with gradient background
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #1976D2, stop:1 #2196F3);
                border-radius: 15px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(10)  # Reduced spacing
        
        # Title label
        title_label = QLabel("Admin Credentials Update")
        title_label.setFont(QFont('Helvetica', 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: white;")
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle = QLabel("Update your administrator login credentials securely")
        subtitle.setFont(QFont('Helvetica', 11))
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)
        
        main_layout.addWidget(header_frame)
        
        # Update form - Use QFormLayout for consistent layout
        update_frame = QFrame()
        update_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 10px;
                margin-top: 20px;
            }}
        """)
        form_layout = QFormLayout(update_frame)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(10)
        
        # Current email field with similar styling
        current_email_label = QLabel("Current Email:")
        current_email_label.setFont(QFont('Helvetica', 14))
        form_layout.addRow(current_email_label)
        
        self.current_email_input = QLineEdit()
        self.current_email_input.setPlaceholderText("Enter your current email")
        self.current_email_input.setMinimumHeight(70)
        self.current_email_input.setFont(QFont('Helvetica', 16))
        self.current_email_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px 15px;
                background-color: white;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        form_layout.addRow(self.current_email_input)
        
        # Current password field
        current_password_label = QLabel("Current Password:")
        current_password_label.setFont(QFont('Helvetica', 14))
        form_layout.addRow(current_password_label)
        
        self.current_password_input = QLineEdit()
        self.current_password_input.setPlaceholderText("Enter your current password")
        self.current_password_input.setEchoMode(QLineEdit.Password)
        self.current_password_input.setMinimumHeight(70)
        self.current_password_input.setFont(QFont('Helvetica', 16))
        self.current_password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px 15px;
                background-color: white;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        form_layout.addRow(self.current_password_input)
        
        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        separator.setMinimumHeight(2)
        form_layout.addRow(separator)
        
        # New email field
        new_email_label = QLabel("New Email (optional):")
        new_email_label.setFont(QFont('Helvetica', 14))
        form_layout.addRow(new_email_label)
        
        self.new_email_input = QLineEdit()
        self.new_email_input.setPlaceholderText("Enter new email (leave blank to keep current)")
        self.new_email_input.setMinimumHeight(70)
        self.new_email_input.setFont(QFont('Helvetica', 16))
        self.new_email_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px 15px;
                background-color: white;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        form_layout.addRow(self.new_email_input)
        
        # New password field
        new_password_label = QLabel("New Password:")
        new_password_label.setFont(QFont('Helvetica', 14))
        form_layout.addRow(new_password_label)
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Enter new password")
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setMinimumHeight(70)
        self.new_password_input.setFont(QFont('Helvetica', 16))
        self.new_password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px 15px;
                background-color: white;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        form_layout.addRow(self.new_password_input)
        
        # Confirm new password field
        confirm_password_label = QLabel("Confirm New Password:")
        confirm_password_label.setFont(QFont('Helvetica', 14))
        form_layout.addRow(confirm_password_label)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm new password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setMinimumHeight(70)
        self.confirm_password_input.setFont(QFont('Helvetica', 16))
        self.confirm_password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px 15px;
                background-color: white;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        form_layout.addRow(self.confirm_password_input)
        
        main_layout.addWidget(update_frame)
        
        # Update button with same styling as login button
        update_btn = QPushButton("Update Credentials")
        update_btn.setMinimumHeight(70)
        update_btn.setFont(QFont('Helvetica', 14, QFont.Bold))
        update_btn.setStyleSheet("""
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
        update_btn.clicked.connect(self.update_credentials)
        main_layout.addWidget(update_btn)
        
        # Back to login link with similar style to signup
        back_link = QLabel("Return to <a href='#' style='color:#2196F3;'>Login</a>")
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
    
    def update_credentials(self):
        """Handle admin credentials update"""
        # Get input values
        current_email = self.current_email_input.text().strip()
        current_password = self.current_password_input.text().strip()
        new_email = self.new_email_input.text().strip()
        new_password = self.new_password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
        
        # Validate input - require current credentials
        if not current_email or not current_password:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter your current email and password to authenticate."
            )
            return
        
        # Check if any changes were requested
        if not new_email and not new_password:
            QMessageBox.warning(
                self,
                "No Changes",
                "Please provide either a new email or a new password to update."
            )
            return
        
        # Validate new password if provided
        if new_password:
            if len(new_password) < 6:
                QMessageBox.warning(
                    self,
                    "Password Too Short",
                    "New password must be at least 6 characters long."
                )
                return
            
            if new_password != confirm_password:
                QMessageBox.warning(
                    self,
                    "Password Mismatch",
                    "New password and confirmation do not match."
                )
                return
        
        # Show progress dialog during update process
        progress = QProgressDialog("Updating credentials...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Please Wait")
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        
        # First verify current credentials by attempting to sign in
        auth_result = self.firebase_auth.sign_in(current_email, current_password)
        
        if not auth_result["success"]:
            progress.close()
            QMessageBox.warning(
                self,
                "Authentication Failed",
                "Current email and password are incorrect. Please try again."
            )
            return
        
        # Check if the authenticated user is indeed an admin
        if auth_result["role"].lower() != "admin":
            progress.close()
            QMessageBox.warning(
                self,
                "Not Authorized",
                "Only admin accounts can be updated through this interface."
            )
            return
        
        # Begin the update process
        update_successful = False
        email_to_return = current_email
        
        try:
            # Update password if requested
            if new_password:
                password_result = self.firebase_auth.update_password(current_email, current_password, new_password)
                if not password_result["success"]:
                    progress.close()
                    QMessageBox.warning(
                        self,
                        "Password Update Failed",
                        f"Failed to update password: {password_result.get('message', 'Unknown error')}"
                    )
                    return
            
            # Update email if requested
            if new_email:
                email_result = self.firebase_auth.update_email(current_email, current_password, new_email)
                if not email_result["success"]:
                    progress.close()
                    QMessageBox.warning(
                        self,
                        "Email Update Failed",
                        f"Failed to update email: {email_result.get('message', 'Unknown error')}"
                    )
                    return
                email_to_return = new_email
            
            # If we got here, updates were successful
            update_successful = True
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred during the update process: {str(e)}"
            )
            return
        
        # Close progress dialog
        progress.close()
        
        if update_successful:
            # Emit signal with updated email
            self.update_successful.emit(email_to_return)
            
            # Close the window
            self.close()
        
    def back_to_login(self):
        """Go back to login screen"""
        self.update_cancelled.emit()
        self.close()
        
    def closeEvent(self, event):
        """Handle window close event"""
        # If closed without completing update, emit cancelled signal
        self.update_cancelled.emit()
        event.accept()