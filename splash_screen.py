import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QProgressBar, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        # Increase window size and adjust geometry
        splash_width = 800
        splash_height = 600
        # Remove window title bar and make frameless
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set fixed size for splash screen
        self.resize(splash_width, splash_height)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        # Create main container
        container = QFrame(self)
        container.setObjectName("container")
        container.setGeometry(0, 0, splash_width, splash_height)
        
        # Setup background
        try:
            bg_label = QLabel(container)
            pixmap = QPixmap("bg.jpg").scaled(splash_width, splash_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            bg_label.setPixmap(pixmap)
            bg_label.setGeometry(0, 0, splash_width, splash_height)
        except:
            # Fallback to styled background if image not found
            pass

        # Create layout
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        self.title = QLabel("Ransomware Detection & Prevention")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont('Helvetica', 16, QFont.Bold))  # Reduced from 28
        self.title.setStyleSheet("color: #1976D2;")
        layout.addWidget(self.title)
        
        # Subtitle
        self.subtitle = QLabel("Powered by Moving Target Defense")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setFont(QFont('Helvetica', 12))  # Reduced from 14
        self.subtitle.setStyleSheet("color: #666666;")
        layout.addWidget(self.subtitle)
        
        # Add spacing
        layout.addStretch()
        
        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setFixedSize(400, 8)
        self.progress.setAlignment(Qt.AlignCenter)
        self.progress.setFormat("")  # Remove percentage text
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #E0E0E0;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: #1976D2;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress, alignment=Qt.AlignCenter)
        
        # Status Label
        self.status = QLabel("Initializing...")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setFont(QFont('Helvetica', 12))
        self.status.setStyleSheet("color: #666666;")
        layout.addWidget(self.status)
        
        # Add bottom spacing
        layout.addStretch()
        
        # Setup styling
        self.setStyleSheet("""
            #container {
                background-color: white;
                border-radius: 20px;
            }
        """)
        
        # Initialize progress
        self.progress_value = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(30)

    def update_progress(self):
        self.progress_value += 1
        self.progress.setValue(self.progress_value)
        
        # Update status text
        if self.progress_value < 30:
            self.status.setText("Loading components...")
        elif self.progress_value < 60:
            self.status.setText("Initializing security modules...")
        elif self.progress_value < 90:
            self.status.setText("Starting application...")
        else:
            self.status.setText("Ready to launch...")
        
        # When complete
        if self.progress_value >= 100:
            self.timer.stop()
            QTimer.singleShot(500, self.launch_main_app)

    def launch_main_app(self):
        from components.role_page import RolePage  # Updated import
        self.close()
        self.role_window = RolePage()
        self.role_window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()
    sys.exit(app.exec_())