"""
LumenOrb v2.0 - Log Widget
Read-only log stream with auto-scroll and color-coded messages
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt6.QtGui import QTextCursor
from typing import Literal


class LogWidget(QWidget):
    """
    Log stream display with color-coded status messages
    """
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        """Build the log UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Label
        label = QLabel("System Log:")
        label.setStyleSheet("color: #737373; font-size: 11px;")
        layout.addWidget(label)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setObjectName("logStream")
        self.log_display.setReadOnly(True)
        
        layout.addWidget(self.log_display)
    
    def log(
        self,
        message: str,
        level: Literal["info", "success", "error", "warning"] = "info"
    ):
        """
        Add a log message
        
        Args:
            message: Message text
            level: Message severity level
        """
        # Color mapping
        color_map = {
            "info": "#4488FF",
            "success": "#00FF88",
            "error": "#FF4444",
            "warning": "#FFAA00"
        }
        
        color = color_map.get(level, "#737373")
        
        # Format message with HTML color
        formatted = f'<span style="color: {color};">{message}</span>'
        
        # Append to log
        self.log_display.append(formatted)
        
        # Auto-scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_display.setTextCursor(cursor)
    
    def clear(self):
        """Clear all log messages"""
        self.log_display.clear()
