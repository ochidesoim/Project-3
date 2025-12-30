"""
LumenOrb v2.0 - Viewport Widget
PyVista 3D rendering embedded in PyQt6
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame
from pathlib import Path

try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False


class ViewportWidget(QWidget):
    """
    3D viewport for mesh visualization using PyVista
    """
    
    def __init__(self):
        super().__init__()
        
        self.current_mesh = None
        self._init_ui()
    
    def _init_ui(self):
        """Build the viewport UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Container frame
        frame = QFrame()
        frame.setObjectName("viewportFrame")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        
        if PYVISTA_AVAILABLE:
            # Create PyVista Qt interactor
            self.plotter = QtInteractor(frame)
            self.plotter.set_background("#0A0A0A")  # Match darkroom theme
            
            # Add grid (lighter color for better visibility on dark background)
            self.plotter.show_grid(
                color="#3A3A3A",
                font_size=10
            )
            
            frame_layout.addWidget(self.plotter.interactor)
        else:
            # Fallback if PyVista not installed
            from PyQt6.QtWidgets import QLabel
            from PyQt6.QtCore import Qt
            
            label = QLabel("PyVista not installed\nRun: pip install pyvista pyvistaqt")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #FF4444; font-size: 14px;")
            frame_layout.addWidget(label)
        
        layout.addWidget(frame)
    
    def load_mesh(self, mesh_path: Path):
        """
        Load and display an STL mesh
        
        Args:
            mesh_path: Path to STL file
        """
        if not PYVISTA_AVAILABLE:
            return
        
        try:
            # Clear previous mesh
            self.plotter.clear()
            
            # Load mesh
            mesh = pv.read(str(mesh_path))
            
            # Add to plotter
            self.plotter.add_mesh(
                mesh,
                color="#E0E0E0",
                show_edges=True,
                edge_color="#3A3A3A",
                lighting=True,
                smooth_shading=True
            )
            
            # Reset camera
            self.plotter.reset_camera()
            
            # Re-add grid (lighter color for better visibility on dark background)
            self.plotter.show_grid(
                color="#3A3A3A",
                font_size=10
            )
            
            self.current_mesh = mesh_path
            
        except Exception as e:
            print(f"Error loading mesh: {e}")
    
    def clear(self):
        """Clear the viewport"""
        if PYVISTA_AVAILABLE:
            self.plotter.clear()
            self.current_mesh = None
