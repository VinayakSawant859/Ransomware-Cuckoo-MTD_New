from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFrame, QScrollArea, QSpacerItem,
                           QSizePolicy, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QDateTime
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap
import os
import time

class ExitTab(QWidget):
    """Tab for user information and application exit"""
    
    # Signal to notify main window about logout
    logout_requested = pyqtSignal()
    
    def __init__(self, parent=None, user_info=None):
        super().__init__(parent)
        # Set default user info if None is provided
        self.user_info = user_info or {"email": "user@example.com", "role": "admin"}
        
        # Make sure the role is a string, not None
        if "role" not in self.user_info or self.user_info["role"] is None:
            self.user_info["role"] = "admin"
            
        # Make sure the email is a string, not None
        if "email" not in self.user_info or self.user_info["email"] is None:
            self.user_info["email"] = "user@example.com"
            
        # Store login time for active time tracking
        self.login_time = QDateTime.currentDateTime()
            
        self.initUI()
        
    def initUI(self):
        # Main layout with scroll area for better responsiveness
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(60, 60, 60, 60)  # Larger margins for better spacing
        scroll_layout.setSpacing(30)  # Moderate spacing between sections
        
        # ===== PROFILE SECTION =====
        # Create a horizontal layout for the top cards
        top_cards_layout = QHBoxLayout()
        top_cards_layout.setSpacing(20)  # Space between cards
        
        # Profile picture card
        profile_pic_card = self.create_card(
            icon="⚙️",
            title=self.user_info.get("email", "user@example.com").split('@')[0],
            subtitle="Profile",
            gradient=["#2196F3", "#0D47A1"]
        )
        top_cards_layout.addWidget(profile_pic_card)
        
        # User role card
        role = self.user_info.get("role", "admin")
        role_display = role.title() if isinstance(role, str) else "Admin"
        role_card = self.create_card(
            icon="👤",
            title=role_display,
            subtitle="User Role",
            gradient=["#4CAF50", "#2E7D32"]
        )
        top_cards_layout.addWidget(role_card)
        
        # Active time card
        active_card = self.create_card(
            icon="⏱️",
            title="Active Time",
            subtitle=self.calculate_active_time(),
            gradient=["#FF9800", "#E65100"]
        )
        # Update the active time every minute
        self.timer = self.startTimer(60000)  # 60000 ms = 1 minute
        self.active_time_card = active_card
        top_cards_layout.addWidget(active_card)
        
        scroll_layout.addLayout(top_cards_layout)
        
        # ===== EMAIL INFORMATION SECTION =====
        email_section = QFrame()
        email_section.setObjectName("emailSection")
        email_section.setStyleSheet("""
            QFrame#emailSection {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        email_section.setGraphicsEffect(shadow)
        
        email_layout = QVBoxLayout(email_section)
        email_layout.setContentsMargins(25, 25, 25, 25)
        
        # Email section title
        email_title = QLabel("Account Information")
        email_title.setFont(QFont('Helvetica', 16, QFont.Bold))
        email_title.setStyleSheet("color: #333333;")
        email_layout.addWidget(email_title)
        
        # Email address with icon
        email_container = QHBoxLayout()
        email_icon = QLabel("📧")
        email_icon.setFont(QFont('Segoe UI Emoji', 16))
        email_container.addWidget(email_icon)
        
        email_address = QLabel(self.user_info.get("email", "user@example.com"))
        email_address.setFont(QFont('Helvetica', 14))
        email_address.setStyleSheet("color: #555555;")
        email_container.addWidget(email_address)
        email_container.addStretch()
        
        email_layout.addLayout(email_container)
        email_layout.addSpacing(10)
        
        # Login information
        login_title = QLabel("Login Information")
        login_title.setFont(QFont('Helvetica', 14, QFont.Bold))
        login_title.setStyleSheet("color: #333333;")
        email_layout.addWidget(login_title)
        
        # Login time with icon
        login_container = QHBoxLayout()
        login_icon = QLabel("🕒")
        login_icon.setFont(QFont('Segoe UI Emoji', 16))
        login_container.addWidget(login_icon)
        
        login_time = QLabel(f"Logged in: {self.login_time.toString('yyyy-MM-dd hh:mm:ss')}")
        login_time.setFont(QFont('Helvetica', 12))
        login_time.setStyleSheet("color: #555555;")
        login_container.addWidget(login_time)
        login_container.addStretch()
        
        email_layout.addLayout(login_container)
        
        scroll_layout.addWidget(email_section)
        
        # ===== ABOUT SECTION =====
        about_section = QFrame()
        about_section.setObjectName("aboutSection")
        about_section.setStyleSheet("""
            QFrame#aboutSection {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Add shadow effect
        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(10)
        shadow2.setColor(QColor(0, 0, 0, 30))
        shadow2.setOffset(0, 3)
        about_section.setGraphicsEffect(shadow2)
        
        about_layout = QVBoxLayout(about_section)
        about_layout.setContentsMargins(25, 25, 25, 25)
        
        # About title
        about_title = QLabel("About This Application")
        about_title.setFont(QFont('Helvetica', 16, QFont.Bold))
        about_title.setStyleSheet("color: #333333;")
        about_layout.addWidget(about_title)
        
        # Description text
        description = QLabel(
            "<p style='line-height: 150%;'>Ransomware Cuckoo-MTD is an advanced security application designed to protect your system "
            "against ransomware threats through real-time monitoring and Moving Target Defense (MTD) "
            "techniques.</p>"
            "<p style='line-height: 150%;'>The application continuously scans for suspicious activities, monitors file system changes, "
            "and implements dynamic defense mechanisms to prevent ransomware from encrypting your files.</p>"
            "<p style='line-height: 150%;'>Developed by Pillai HOC College of Engineering as part of ongoing Final Year Project "
            "by <b>Rashmi Patil</b>, <b>Sanika Patil</b>, and <b>Sanika Shinde</b>.</p>"
        )
        description.setFont(QFont('Helvetica', 11))
        description.setStyleSheet("color: #555555;")
        description.setWordWrap(True)
        about_layout.addWidget(description)
        
        # Version info
        version_container = QHBoxLayout()
        version_container.addStretch()
        
        version_label = QLabel("Version 1.0.0")
        version_label.setFont(QFont('Helvetica', 10))
        version_label.setStyleSheet("color: #888888;")
        version_container.addWidget(version_label)
        
        about_layout.addLayout(version_container)
        
        scroll_layout.addWidget(about_section)
        
        # ===== LOGOUT BUTTON =====
        scroll_layout.addStretch(1)  # Push everything up
        
        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setFixedSize(200, 60)
        logout_btn.setFont(QFont('Helvetica', 14, QFont.Bold))
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 30px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:pressed {
                background-color: #B71C1C;
            }
        """)
        
        # Add icon to logout button if available
        try:
            icon_path = os.path.join("drawable", "logout_icon.png")
            if os.path.exists(icon_path):
                logout_btn.setIcon(QIcon(icon_path))
                logout_btn.setIconSize(QSize(24, 24))
        except:
            pass
            
        logout_btn.clicked.connect(self.logout)
        scroll_layout.addWidget(logout_btn, alignment=Qt.AlignCenter)
        
        # Set up scroll area
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
    
    def create_card(self, icon, title, subtitle, gradient=None):
        """Create a styled info card with icon and content"""
        card = QFrame()
        card.setFixedSize(180, 180)  # Square cards with fixed size
        
        # Set gradient background if provided
        if (gradient):
            card.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                              stop:0 {gradient[0]}, stop:1 {gradient[1]});
                    border-radius: 15px;
                }}
            """)
        else:
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 15px;
                    border: 1px solid #e0e0e0;
                }
            """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 20, 15, 20)
        card_layout.setSpacing(10)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont('Segoe UI Emoji', 26))  # Large emoji font
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("color: white; background: transparent;")
        card_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont('Helvetica', 12, QFont.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        card_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(QFont('Helvetica', 10))
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background: transparent;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle_label)
        
        return card
    
    def calculate_active_time(self):
        """Calculate and format the active time since login"""
        current_time = QDateTime.currentDateTime()
        seconds = self.login_time.secsTo(current_time)
        
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"
    
    def timerEvent(self, event):
        """Update the active time display every minute"""
        if hasattr(self, 'active_time_card') and self.active_time_card:
            # Find the subtitle label (it's the third widget in the layout)
            layout = self.active_time_card.layout()
            if layout and layout.count() >= 3:
                subtitle_label = layout.itemAt(2).widget()
                if isinstance(subtitle_label, QLabel):
                    subtitle_label.setText(self.calculate_active_time())
    
    def set_user_info(self, user_info):
        """Update the user information displayed"""
        # Ensure we have valid user info
        self.user_info = user_info or {"email": "user@example.com", "role": "admin"}
        
        # Make sure the role is a string, not None
        if "role" not in self.user_info or self.user_info["role"] is None:
            self.user_info["role"] = "admin"
            
        # This would need to refresh the UI elements
        # For simplicity, we just recreate the UI
        # In a real application, you might want to update specific widgets
        for i in reversed(range(self.layout().count())): 
            self.layout().itemAt(i).widget().setParent(None)
        self.initUI()
    
    def logout(self):
        """Handle logout button click"""
        self.logout_requested.emit()
