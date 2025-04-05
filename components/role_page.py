from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                           QLabel, QFrame, QApplication, QGraphicsDropShadowEffect, QHBoxLayout)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap
from .login import LoginWindow

class RolePage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Select Role")
        self.setFixedSize(1200, 1200)
        
        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(100, 60, 100, 60)  # Adjusted margins
        layout.setSpacing(30)  # Reduced spacing
        
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
        
        # Header section - reduced padding and font sizes
        header_frame = QFrame()
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(15)
        header_shadow.setColor(QColor(0, 0, 0, 30))
        header_shadow.setOffset(0, 2)
        header_frame.setGraphicsEffect(header_shadow)
        
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
        
        # Welcome text - smaller fonts
        welcome_label = QLabel("Welcome to")
        welcome_label.setFont(QFont('Helvetica', 16))  # Reduced from 20
        welcome_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        welcome_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(welcome_label)
        
        title_label = QLabel("Ransomware Detection System")
        title_label.setFont(QFont('Helvetica', 20, QFont.Bold))  # Reduced from 24
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        layout.addWidget(header_frame)
        
        # Role selection text - adjusted size
        select_label = QLabel("Select your role to continue")
        select_label.setFont(QFont('Helvetica', 14))  # Reduced from 16
        select_label.setStyleSheet("color: #666666; margin: 15px 0;")
        select_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(select_label)
        
        # Buttons container - adjusted padding
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 15px;
                padding: 25px;
            }
        """)
        
        buttons_layout = QVBoxLayout(buttons_frame)
        buttons_layout.setSpacing(20)  # Reduced spacing
        
        # Role buttons - reduced size and padding
        roles = [
            ("student", "Login as Student", "#2196F3", "#1976D2", "👨‍🎓"),
            ("faculty", "Login as Faculty", "#4CAF50", "#388E3C", "👨‍🏫"),
            ("admin", "Login as Admin", "#FF5722", "#D84315", "⚙️")
        ]
        
        for role, text, color, hover_color, icon in roles:
            btn = QPushButton(f" {icon}  {text}")
            btn.setFixedSize(600, 70)  # Reduced size
            btn.setFont(QFont('Helvetica', 14, QFont.Bold))  # Reduced font size
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    text-align: left;
                    padding-left: 30px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
            """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, r=role: self.show_login(r))
            buttons_layout.addWidget(btn, alignment=Qt.AlignCenter)
        
        layout.addWidget(buttons_frame)
        
        # Footer - reduced font size
        footer = QLabel("Choose your role carefully to access appropriate features")
        footer.setFont(QFont('Helvetica', 11))  # Reduced from 12
        footer.setStyleSheet("color: #666666;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)
        
        # Add stretches for better vertical distribution
        layout.insertStretch(0, 1)
        layout.addStretch(1)
        
        self.center_window()

    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def show_login(self, role):
        self.login_window = LoginWindow(role)
        self.login_window.show()
        self.hide()
        
        # Connect signals after showing window
        self.login_window.user_authenticated.connect(self.on_login_success)
        self.login_window.login_cancelled.connect(self.show)

    def on_login_success(self, user_email, user_role):
        from main import RansomwareApp
        self.main_window = RansomwareApp(None, user_email, user_role)
        self.main_window.show()
        self.close()
