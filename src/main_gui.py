"""
LumenOrb v2.0 - Hyper-Realism Architecture
Framework: PyQt6 + PyVistaQt
Theme: Midnight Stealth (Deep Obsidian / Emerald / Indigo)
Features: PBR, Auto-Smoothing, Eye Dome Lighting
"""

import sys
import os
import time
import warnings
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QTextEdit, QLabel, QSplitter, QFrame, QTableWidget, 
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QFileSystemWatcher
from pyvistaqt import QtInteractor
import pyvista as pv

# Suppress Warnings
warnings.simplefilter("ignore")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent import Agent
from core.compiler import AtomicCompiler

# --- THEME CONSTANTS ---
C_BG = "#121212"
C_PANEL = "#1E1E1E"
C_BORDER = "#2D2D2D"
C_INPUT = "#181818"
C_ACCENT_A = "#00BFA5" # Emerald
C_ACCENT_B = "#5C6BC0" # Indigo
C_TEXT_MAIN = "#E0E0E0"
C_TEXT_DIM = "#757575"

STYLESHEET = f"""
QMainWindow {{ background-color: {C_BG}; color: {C_TEXT_MAIN}; }}
QWidget {{ font-family: "Segoe UI", sans-serif; font-size: 13px; color: {C_TEXT_MAIN}; }}
QFrame {{ border: 1px solid {C_BORDER}; border-radius: 4px; background-color: {C_PANEL}; }}
QLineEdit {{ background-color: {C_INPUT}; color: {C_ACCENT_A}; border: 1px solid {C_BORDER}; padding: 8px; font-family: "Consolas", monospace; }}
QLineEdit:focus {{ border: 1px solid {C_ACCENT_B}; }}
QTextEdit {{ background-color: {C_PANEL}; color: {C_TEXT_DIM}; border: none; font-family: "Consolas", monospace; font-size: 11px; }}
QLabel {{ border: none; background: transparent; }}
QTableWidget {{ background-color: {C_PANEL}; gridline-color: {C_BORDER}; border: none; }}
QHeaderView::section {{ background-color: {C_INPUT}; padding: 4px; border: none; color: {C_TEXT_DIM}; }}
QTableCornerButton::section {{ background-color: {C_INPUT}; border: none; }}
"""

class WorkerThread(QThread):
    finished = pyqtSignal(dict)
    log = pyqtSignal(str, str) # msg, color

    def __init__(self, agent, compiler, user_input):
        super().__init__()
        self.agent = agent
        self.compiler = compiler
        self.user_input = user_input

    def run(self):
        try:
            self.log.emit(f"Analyzing: {self.user_input}...", C_ACCENT_B)
            # USES ACTUAL API: solve_problem, not process
            result = self.agent.solve_problem(self.user_input)
            
            mode = result.get("mode", "unknown").upper()
            self.log.emit(f"Mode: {mode}", C_ACCENT_A)
            
            self.log.emit("Compiling Geometry...", C_TEXT_DIM)
            json_path = self.compiler.compile(result)
            
            if json_path:
                self.log.emit("Geometry Generated.", "#00FF00")
            else:
                self.log.emit("Generation Failed.", "#FF0000")
                
            self.finished.emit(result)
            
        except Exception as e:
            self.log.emit(f"Error: {e}", "#FF0000")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOYRON: COMPUTATIONAL ENGINEERING [PBR MODE]")
        self.resize(1600, 900)
        self.setStyleSheet(STYLESHEET)
        
        # Init Core
        self.setup_core()
        
        # UI Layout
        self.init_ui()
        
        # File Watcher for Live Rendering
        self.watcher = QFileSystemWatcher()
        
        # USES ACTUAL PATH: render.stl (C# Output)
        self.render_file = Path.cwd() / "picogk_runner" / "render.stl"
        
        if self.render_file.parent.exists():
            self.watcher.addPath(str(self.render_file.parent))
            self.watcher.directoryChanged.connect(self.check_render_file)
            self.watcher.fileChanged.connect(self.reload_mesh)
            
            if self.render_file.exists():
                self.reload_mesh(str(self.render_file))

    def setup_core(self):
        try:
            self.root = Path(__file__).parent.parent
            self.agent = Agent(
                system_prompt_path=self.root / "resources" / "system_prompt.txt",
                cheatsheet_path=self.root / "resources" / "picogk_cheatsheet.md",
                local_model_name="qwen2.5-coder:latest"
            )
            self.compiler = AtomicCompiler()
        except Exception as e:
            print(f"Core Init Error: {e}")

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- LEFT PANEL ---
        left_frame = QFrame()
        left_frame.setFixedWidth(400)
        left_layout = QVBoxLayout(left_frame)
        
        title = QLabel("NOYRON")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        subtitle = QLabel("COMPUTATIONAL ENGINEERING")
        subtitle.setStyleSheet(f"font-size: 12px; color: {C_ACCENT_B}; letter-spacing: 2px;")
        
        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)
        left_layout.addSpacing(20)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        left_layout.addWidget(self.log_view)
        
        self.param_table = QTableWidget()
        self.param_table.setColumnCount(2)
        self.param_table.setHorizontalHeaderLabels(["PARAM", "VALUE"])
        self.param_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.param_table.verticalHeader().setVisible(False)
        self.param_table.setFixedHeight(200)
        left_layout.addWidget(QLabel("PARAMETERS"))
        left_layout.addWidget(self.param_table)
        
        self.input_field = QLineEdit()
        self.input_field.setMinimumHeight(40)
        self.input_field.setPlaceholderText("> Enter intent (e.g. 'Rocket, thrust 50')")
        self.input_field.returnPressed.connect(self.process_input)
        
        left_layout.addWidget(QLabel("COMMAND INPUT"))
        left_layout.addWidget(self.input_field)
        
        # --- RIGHT PANEL (HYPER-REALISM VIEWPORT) ---
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0,0,0,0)
        
        self.plotter = QtInteractor(right_frame)
        
        # 1. Gradient Background (Premium CAD Lock)
        self.plotter.set_background("#1a1a1a", top="#000000")
        
        # 2. Studio Lighting & Anti-Aliasing
        self.plotter.enable_eye_dome_lighting() # EDL for depth/shadows
        self.plotter.enable_anti_aliasing()
        self.plotter.add_axes()
        
        right_layout.addWidget(self.plotter.interactor)
        
        splitter.addWidget(left_frame)
        splitter.addWidget(right_frame)
        layout.addWidget(splitter)

    def log(self, msg, color=C_TEXT_MAIN):
        timestamp = time.strftime("%H:%M:%S")
        html = f"<span style='color:{C_TEXT_DIM}'>[{timestamp}]</span> <span style='color:{color}'>{msg}</span>"
        self.log_view.append(html)

    def process_input(self):
        text = self.input_field.text().strip()
        if not text: return
        self.input_field.clear()
        self.log(f"> {text}", "white")
        self.worker = WorkerThread(self.agent, self.compiler, text)
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self.on_process_finished)
        self.worker.start()

    def on_process_finished(self, result):
        self.param_table.setRowCount(0)
        if result.get("mode") == "engineering":
            meta = result.get("meta", {})
            params = meta.get("extracted_params", {})
            self.param_table.setRowCount(len(params))
            for i, (k, v) in enumerate(params.items()):
                self.param_table.setItem(i, 0, QTableWidgetItem(str(k)))
                self.param_table.setItem(i, 1, QTableWidgetItem(str(v)))
        
        # Load mesh from correct path
        if self.render_file.exists():
             self.reload_mesh(str(self.render_file))

    def check_render_file(self, path):
        if self.render_file.exists():
            self.reload_mesh(str(self.render_file))

    def reload_mesh(self, path):
        try:
            file_path = str(path)
            self.log(f"Polishing: {Path(file_path).name}...", C_ACCENT_B)
            
            raw_mesh = pv.read(file_path)
            if not raw_mesh or raw_mesh.n_points == 0:
                self.log("Error: Mesh is empty.", "#FF0000")
                return

            # --- CAD SMOOTHING PIPELINE ---
            # 1. Subdivide: Increase resolution to allow finer smoothing
            refined = raw_mesh.subdivide(1, subfilter='linear')
            
            # 2. Aggressive Smoothing: Melt voxel artifacts
            sleek_mesh = refined.smooth(n_iter=100, relaxation_factor=0.08)
            
            # 3. Compute Normals: Critical for "AutoCAD" smooth shading
            # This makes the light reflect smoothly across curved surfaces
            sleek_mesh = sleek_mesh.compute_normals(cell_normals=False, point_normals=True, auto_orient_normals=True)
            
            self.plotter.clear()
            
            # --- TITANIUM PBR MATERIAL ---
            # Hyper-Realism Mode
            self.plotter.add_mesh(
                sleek_mesh,
                color="#C0C0C0",        # Silver/Titanium Base
                pbr=True,               # Physically Based Rendering
                metallic=1.0,           # 100% Metal
                roughness=0.3,          # Slightly brushed
                diffuse=0.8,
                specular=1.0,
                smooth_shading=True
            )
            
            self.plotter.reset_camera()
            self.plotter.view_isometric()
            
            self.log(f"Render Complete ({sleek_mesh.n_points} pts).", "#00FF00")
            
        except Exception as e:
            self.log(f"Render Error: {e}", "#FF0000")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
