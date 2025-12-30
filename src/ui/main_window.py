"""
LumenOrb v2.0 - Main Window
The "Bento Grid" Layout: 30% Left (Log + Console) / 70% Right (Viewport)
Uses QThread to prevent UI freezing during AI queries
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from pathlib import Path
import psutil
import os

from src.ui.console_widget import ConsoleWidget
from src.ui.log_widget import LogWidget
from src.ui.viewport import ViewportWidget
from src.core.agent import Agent
from src.core.session import SessionManager
from src.core.template_engine import TemplateEngine
from src.core.execution import ExecutionEngine
from src.core.models import GeometryRequest
from src.core.recipe import RecipeExecutor, GeometryRecipe
from src.core.compiler import AtomicCompiler
from src.core.runner import PicoRunner


class AIWorker(QThread):
    """Background thread for AI queries to prevent UI freezing"""
    
    finished = pyqtSignal(object)  # Emits GeometryRequest or Exception
    status = pyqtSignal(str)       # Progress updates
    
    def __init__(self, agent: Agent, user_text: str, model: str = "local"):
        super().__init__()
        self.agent = agent
        self.user_text = user_text
        self.model = model
    
    def run(self):
        try:
            self.status.emit("Querying AI (this may take a moment)...")
            request = self.agent.query(self.user_text, model=self.model)
            self.finished.emit(request)
        except Exception as e:
            self.finished.emit(e)


class MainWindow(QMainWindow):
    """
    Main application window with Bento grid layout
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("LumenOrb v2.0 - Agentic Computational Engineering")
        self.setGeometry(100, 100, 1600, 900)
        
        # Track background worker
        self.ai_worker = None
        self.pending_user_text = None
        
        # Initialize core systems
        self._init_systems()
        
        # Build UI
        self._init_ui()
        
        # Start telemetry updates
        self._start_telemetry()
    
    def _init_systems(self):
        """Initialize backend systems"""
        project_root = Path(__file__).parent.parent.parent
        
        # Session manager
        self.session_manager = SessionManager(project_root / "output")
        self.session_manager.create_session()
        
        # Template engine (legacy mode)
        template_dir = project_root / "src" / "computational" / "templates"
        self.template_engine = TemplateEngine(template_dir)
        
        # Recipe executor (new atomic composition mode)
        self.recipe_executor = RecipeExecutor()
        
        # Execution engine
        self.execution_engine = ExecutionEngine(max_timeout_seconds=30)
        
        # AI Agent
        from dotenv import load_dotenv
        load_dotenv()
        
        gemini_key = os.getenv("GEMINI_API_KEY")
        local_endpoint = os.getenv("LOCAL_MODEL_ENDPOINT", "http://localhost:11434/v1")
        local_model = os.getenv("LOCAL_MODEL_NAME", "qwen2.5-coder")
        use_recipe_mode = os.getenv("USE_RECIPE_MODE", "true").lower() == "true"
        
        self.agent = Agent(
            system_prompt_path=project_root / "resources" / "system_prompt.txt",
            cheatsheet_path=project_root / "resources" / "picogk_cheatsheet.md",
            gemini_api_key=gemini_key,
            local_endpoint=local_endpoint,
            local_model_name=local_model,
            use_recipe_mode=use_recipe_mode
        )
    
    def _init_ui(self):
        """Build the Bento grid layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Main content area (splitter for 30/70 split)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel (Log + Console)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(4)
        
        # Log stream (top)
        self.log_widget = LogWidget()
        left_layout.addWidget(self.log_widget, stretch=3)
        
        # Console input (bottom)
        self.console_widget = ConsoleWidget()
        self.console_widget.command_submitted.connect(self.on_user_input)
        left_layout.addWidget(self.console_widget, stretch=1)
        
        # Right panel (Viewport)
        self.viewport_widget = ViewportWidget()
        
        # Add to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.viewport_widget)
        
        # Set 30/70 split
        splitter.setSizes([480, 1120])  # 30% / 70% of 1600px
        
        main_layout.addWidget(splitter)
        
        # Telemetry bar (footer)
        self.telemetry_label = QLabel("Initializing...")
        self.telemetry_label.setObjectName("telemetryLabel")
        self.telemetry_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(self.telemetry_label)
        
        # Initial log message
        self.log_widget.log("LumenOrb v2.0 initialized", "info")
        self.log_widget.log(f"Session: {self.session_manager.current_session.session_id}", "info")
        self.log_widget.log("Using local Qwen model via Ollama", "info")
        self.log_widget.log("Ready for input", "success")
    
    def _start_telemetry(self):
        """Start periodic telemetry updates"""
        self.telemetry_timer = QTimer()
        self.telemetry_timer.timeout.connect(self._update_telemetry)
        self.telemetry_timer.start(1000)  # Update every 1 second
        self._update_telemetry()
    
    def _update_telemetry(self):
        """Update hardware telemetry display"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_gb = memory.used / (1024 ** 3)
        memory_total_gb = memory.total / (1024 ** 3)
        
        # GPU stats (requires gputil, may fail if not installed)
        gpu_info = "GPU: N/A"
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_info = f"GPU: {gpu.load * 100:.0f}% | {gpu.memoryUsed:.0f}MB"
        except:
            pass
        
        # Add AI status
        ai_status = "AI: Ready" if not self.ai_worker else "AI: Working..."
        
        telemetry_text = (
            f"CPU: {cpu_percent:.1f}% | "
            f"RAM: {memory_gb:.1f}/{memory_total_gb:.1f}GB | "
            f"{gpu_info} | {ai_status}"
        )
        
        self.telemetry_label.setText(telemetry_text)
    
    def on_user_input(self, user_text: str):
        """
        Handle user input from console
        
        Args:
            user_text: User's command/request
        """
        self.log_widget.log(f"> {user_text}", "info")
        
        # Special commands
        if user_text.lower() in ["clear", "reset"]:
            self.agent.clear_history()
            self.log_widget.log("History cleared", "success")
            return
        
        if user_text.lower() in ["exit", "quit"]:
            self.close()
            return
        
        # Check if already processing
        if self.ai_worker and self.ai_worker.isRunning():
            self.log_widget.log("Already processing a request, please wait...", "warning")
            return
        
        # Store user text for callback
        self.pending_user_text = user_text
        
        # Start AI query in background thread
        self.log_widget.log("Querying AI (running in background)...", "info")
        
        self.ai_worker = AIWorker(self.agent, user_text, model="local")
        self.ai_worker.status.connect(self._on_ai_status)
        self.ai_worker.finished.connect(self._on_ai_finished)
        self.ai_worker.start()
    
    def _on_ai_status(self, message: str):
        """Handle AI status updates"""
        self.log_widget.log(message, "info")
    
    def _on_ai_finished(self, result):
        """
        Handle AI query completion
        
        Args:
            result: GeometryRequest on success, Exception on failure
        """
        if isinstance(result, Exception):
            self.log_widget.log(f"✗ AI Error: {str(result)}", "error")
            return
        
        request = result
        user_text = self.pending_user_text
        
        try:
            self.log_widget.log(f"Mode: {request.mode}", "success")
            self.log_widget.log(f"Intent: {request.intent}", "info")
            
            # Get execution ID
            exec_id = len(self.session_manager.current_session.history) + 1
            
            # Create temporary output directory for this execution
            temp_output_dir = self.session_manager.session_dir / "temp"
            temp_output_dir.mkdir(exist_ok=True)
            final_mesh = self.session_manager.get_mesh_path(exec_id)
            
            if request.mode == "recipe" and request.recipe:
                # Recipe mode: Execute atomic operations
                self.log_widget.log("Executing recipe...", "info")
                
                try:
                    recipe = GeometryRecipe(**request.recipe)
                    
                    # === PICOGK JSON BRIDGE MODE ===
                    # Compiler writes recipe.json and launches pre-compiled engine
                    self.log_widget.log("[PicoGK Mode] Using JSON Bridge...", "info")
                    try:
                        compiler = AtomicCompiler()
                        # compile() now writes JSON and calls run_engine()
                        compiler.compile(request.recipe)
                        self.log_widget.log("✓ PicoGK execution started (viewer may open)", "success")
                        picogk_success = True
                    except Exception as pico_e:
                        self.log_widget.log(f"⚠️ PicoGK error: {pico_e}", "warning")
                        picogk_success = False
                    
                    # Update session
                    self.session_manager.add_execution_result(
                        user_prompt=user_text,
                        ai_model_used="qwen-2.5-local",
                        script_path=None,
                        status="SUCCESS",
                        mesh_path=final_mesh,
                        execution_time_ms=0
                    )
                    
                    # Update agent state
                    self.agent.set_geometry_state(final_mesh)
                    
                    # Load in viewport
                    self.viewport_widget.load_mesh(final_mesh)
                except Exception as e:
                    self.log_widget.log(f"✗ Recipe execution failed: {str(e)}", "error")
                    self.session_manager.add_execution_result(
                        user_prompt=user_text,
                        ai_model_used="qwen-2.5-local",
                        script_path=None,
                        status="FAILURE",
                        error_log=str(e)
                    )
            
            else:
                # Template mode (legacy)
                self.log_widget.log(f"Template: {request.template_id}", "success")
                
                # Render template
                script_path = self.session_manager.get_script_path(exec_id)
                self.template_engine.render(request, script_path)
                self.log_widget.log(f"Script generated: {script_path.name}", "success")
                
                # Execute
                self.log_widget.log("Executing PicoGK script...", "info")
                
                result = self.execution_engine.execute_safe(script_path, temp_output_dir)
                
                if result["status"] == "SUCCESS":
                    # Move output to final location
                    temp_mesh = temp_output_dir / "output.stl"
                    
                    if temp_mesh.exists():
                        temp_mesh.rename(final_mesh)
                        
                        self.log_widget.log(f"✓ Success ({result['execution_time_ms']}ms)", "success")
                        
                        # Update session
                        self.session_manager.add_execution_result(
                            user_prompt=user_text,
                            ai_model_used="qwen-2.5-local",
                            script_path=script_path,
                            mesh_path=final_mesh,
                            execution_time_ms=result["execution_time_ms"]
                        )
                        
                        # Update agent state
                        self.agent.set_geometry_state(final_mesh)
                        
                        # Load in viewport
                        self.viewport_widget.load_mesh(final_mesh)
                    else:
                        self.log_widget.log("✗ No output file generated (PicoGK not installed?)", "error")
                
                else:
                    error_msg = result.get("reason") or result.get("trace", "Unknown error")
                    self.log_widget.log(f"✗ Execution failed: {error_msg}", "error")
                    
                    self.session_manager.add_execution_result(
                        user_prompt=user_text,
                        ai_model_used="qwen-2.5-local",
                        script_path=script_path,
                        status=result["status"],
                        error_log=error_msg
                    )
        
        except Exception as e:
            self.log_widget.log(f"✗ Error: {str(e)}", "error")
