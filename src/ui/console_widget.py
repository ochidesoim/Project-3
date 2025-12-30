"""
LumenOrb v2.0 - Console Widget
Single-line command input with history
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel
from PyQt6.QtCore import pyqtSignal, Qt


class ConsoleWidget(QWidget):
    """
    Command-line style input widget
    """
    
    command_submitted = pyqtSignal(str)  # Emitted when user presses Enter
    
    def __init__(self):
        super().__init__()
        
        self.command_history = []
        self.history_index = -1
        
        self._init_ui()
    
    def _init_ui(self):
        """Build the console UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Label
        label = QLabel("Command:")
        label.setStyleSheet("color: #737373; font-size: 11px;")
        layout.addWidget(label)
        
        # Input field
        self.input_field = QLineEdit()
        self.input_field.setObjectName("consoleInput")
        self.input_field.setPlaceholderText("Describe your geometry...")
        self.input_field.returnPressed.connect(self._on_submit)
        
        layout.addWidget(self.input_field)
    
    def _on_submit(self):
        """Handle Enter key press"""
        text = self.input_field.text().strip()
        
        if not text:
            return
        
        # Add to history
        self.command_history.append(text)
        self.history_index = len(self.command_history)
        
        # Emit signal
        self.command_submitted.emit(text)
        
        # Clear input
        self.input_field.clear()
    
    def keyPressEvent(self, event):
        """Handle arrow keys for command history"""
        if event.key() == Qt.Key.Key_Up:
            if self.history_index > 0:
                self.history_index -= 1
                self.input_field.setText(self.command_history[self.history_index])
        
        elif event.key() == Qt.Key.Key_Down:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.input_field.setText(self.command_history[self.history_index])
            else:
                self.history_index = len(self.command_history)
                self.input_field.clear()
        
        else:
            super().keyPressEvent(event)
