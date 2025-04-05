from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QSize, QRectF, QPoint, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QLinearGradient, QFont
from datetime import datetime
import time

class StatusIndicator(QWidget):
    """Widget to show service status with animated indicator"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status = "unknown"  # unknown, running, stopped, error
        self.setFixedSize(40, 40)
        self.animation_offset = 0
        self.animation_timer_id = None
        self.start_animation()

    def start_animation(self):
        if self.animation_timer_id is None:
            self.animation_timer_id = self.startTimer(50)  # Update every 50ms
    
    def stop_animation(self):
        if self.animation_timer_id is not None:
            self.killTimer(self.animation_timer_id)
            self.animation_timer_id = None
    
    def set_status(self, status):
        self.status = status
        self.update()
        
        # Only animate for certain statuses
        if status in ["running", "scanning"]:
            self.start_animation()
        else:
            self.stop_animation()

    def timerEvent(self, event):
        self.animation_offset = (self.animation_offset + 5) % 360
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Define colors for different statuses
        colors = {
            "unknown": QColor("#9E9E9E"),    # Gray
            "running": QColor("#4CAF50"),    # Green
            "scanning": QColor("#2196F3"),   # Blue
            "stopped": QColor("#F44336"),    # Red
            "error": QColor("#FF9800")       # Orange
        }
        
        # Get color for current status
        color = colors.get(self.status, colors["unknown"])
        
        # Draw the main circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(5, 5, 30, 30)
        
        # For running or scanning status, add animated arc
        if self.status in ["running", "scanning"]:
            pen = QPen(Qt.white)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            
            rect = QRectF(8, 8, 24, 24)
            start_angle = self.animation_offset * 16  # Convert to 16ths of a degree
            span_angle = 240 * 16  # 240 degrees in 16ths
            
            painter.drawArc(rect, start_angle, span_angle)
        
        # Draw status icon in center
        if self.status == "running":
            # Draw play triangle
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(Qt.white))
            
            # Create triangle path
            path = QPainterPath()
            path.moveTo(16, 13)
            path.lineTo(25, 20)
            path.lineTo(16, 27)
            path.closeSubpath()
            
            painter.drawPath(path)
            
        elif self.status == "stopped":
            # Draw stop square
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(Qt.white))
            painter.drawRect(15, 15, 10, 10)
            
        elif self.status == "scanning":
            # Draw scanning animation (rotating lines)
            painter.setPen(QPen(Qt.white, 2))
            
            # Draw 4 lines from center at different angles
            center = QPointF(20, 20)
            for i in range(4):
                angle = (i * 90 + self.animation_offset) % 360
                rad = angle * 3.14159 / 180
                end_x = center.x() + 8 * (1 if i % 2 == 0 else -1) * (0.8 if i < 2 else 1)
                end_y = center.y() + 8 * (1 if i < 2 else -1) * (0.8 if i % 2 != 0 else 1)
                painter.drawLine(center.x(), center.y(), end_x, end_y)
                
        elif self.status == "error":
            # Draw exclamation mark
            painter.setPen(QPen(Qt.white, 3))
            painter.drawLine(20, 15, 20, 22)
            painter.drawPoint(20, 26)
            
        else:  # unknown or default
            # Draw question mark
            painter.setPen(QPen(Qt.white, 3))
            font = painter.font()
            font.setPointSize(14)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QRectF(5, 5, 30, 30), Qt.AlignCenter, "?")

class TimelineWidget(QWidget):
    """Widget to visualize service events in a timeline"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.events = []  # List of event dicts with time, type, description
        self.setStyleSheet("background-color: white; border-radius: 5px;")
        
        # Create shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def set_events(self, events):
        """Set timeline events and update display"""
        self.events = sorted(events, key=lambda e: e['time'])
        self.update()
    
    def paintEvent(self, event):
        if not self.events:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRect(self.rect())
        
        # Define event type colors
        event_colors = {
            "start": QColor("#4CAF50"),    # Green
            "stop": QColor("#F44336"),     # Red
            "scan": QColor("#2196F3"),     # Blue
            "scan_complete": QColor("#673AB7")  # Purple
        }
        
        # Calculate timeline parameters
        margin = 30
        timeline_y = self.height() // 2
        available_width = self.width() - 2 * margin
        
        # Draw the main timeline line
        pen = QPen(QColor("#E0E0E0"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(margin, timeline_y, self.width() - margin, timeline_y)
        
        if not self.events:
            return
            
        # Extract min and max times for scaling
        start_time = self.events[0]['time']
        end_time = self.events[-1]['time']
        
        # If only one event, create a span of at least 1 minute
        if start_time == end_time:
            end_time = datetime.fromtimestamp(start_time.timestamp() + 60)
        
        time_span = (end_time - start_time).total_seconds()
        if time_span <= 0:
            time_span = 60  # Fallback to 1 minute
        
        # Draw events on timeline
        for i, event in enumerate(self.events):
            event_time = event['time']
            event_type = event.get('type', 'unknown')
            
            # Calculate position on timeline
            time_position = (event_time - start_time).total_seconds() / time_span
            x_pos = margin + time_position * available_width
            
            # Alternate between above and below timeline for better readability
            y_direction = -1 if i % 2 == 0 else 1
            
            # Draw vertical connecting line
            event_color = event_colors.get(event_type, QColor("#9E9E9E"))
            pen = QPen(event_color)
            pen.setWidth(2)
            painter.setPen(pen)
            
            line_length = 30
            y_end = timeline_y + y_direction * line_length
            painter.drawLine(int(x_pos), timeline_y, int(x_pos), y_end)
            
            # Draw event point on timeline
            point_radius = 6
            painter.setBrush(QBrush(event_color))
            painter.drawEllipse(int(x_pos) - point_radius, timeline_y - point_radius, 
                              point_radius * 2, point_radius * 2)
            
            # Draw event label
            label_width = 120
            label_height = 30
            label_x = int(x_pos) - label_width // 2
            
            # Ensure label stays within widget bounds
            if label_x < 10:
                label_x = 10
            elif label_x + label_width > self.width() - 10:
                label_x = self.width() - 10 - label_width
            
            label_y = y_end + y_direction * 5
            if y_direction < 0:  # Above timeline
                label_y -= label_height
            
            # Draw label background with rounded corners
            label_rect = QRectF(label_x, label_y, label_width, label_height)
            
            # Use gradient for better visual appearance
            gradient = QLinearGradient(label_rect.topLeft(), label_rect.bottomLeft())
            gradient.setColorAt(0, event_color.lighter(120))
            gradient.setColorAt(1, event_color)
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(label_rect, 8, 8)
            
            # Draw event type text
            painter.setPen(Qt.white)
            font = painter.font()
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)
            
            # Get readable event type
            event_labels = {
                "start": "Service Start",
                "stop": "Service Stop",
                "scan": "Scan Started",
                "scan_complete": "Scan Complete"
            }
            label_text = event_labels.get(event_type, event_type.title())
            
            # Draw text
            painter.drawText(label_rect, Qt.AlignCenter, label_text)
            
            # Draw time below/above the label
            time_font = painter.font()
            time_font.setPointSize(8)
            time_font.setBold(False)
            painter.setFont(time_font)
            
            time_label = event_time.strftime("%H:%M:%S")
            time_rect = QRectF(label_x, label_y + label_height * (1 if y_direction > 0 else -0.5),
                             label_width, 20)
            painter.drawText(time_rect, Qt.AlignCenter, time_label)
