"""
LumenOrb v2.0 - Session Manager
Handles session directories, manifest.json, and execution tracking
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.core.models import SessionMetadata, ExecutionResult


class SessionManager:
    """
    Manages session state, output directories, and manifest.json
    """
    
    def __init__(self, base_output_dir: Path):
        """
        Initialize session manager
        
        Args:
            base_output_dir: Base directory for all sessions (e.g., 'output/')
        """
        self.base_output_dir = base_output_dir
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_session: Optional[SessionMetadata] = None
        self.session_dir: Optional[Path] = None
    
    def create_session(self) -> Path:
        """
        Create a new session directory with timestamp
        
        Returns:
            Path to the new session directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{timestamp}"
        
        self.session_dir = self.base_output_dir / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.session_dir / "logs").mkdir(exist_ok=True)
        (self.session_dir / "meshes").mkdir(exist_ok=True)
        (self.session_dir / "scripts").mkdir(exist_ok=True)
        
        # Initialize metadata
        self.current_session = SessionMetadata(
            session_id=session_id,
            hardware_profile="HP OMEN 16",
            history=[]
        )
        
        self._save_manifest()
        
        return self.session_dir
    
    def load_session(self, session_dir: Path) -> SessionMetadata:
        """
        Load an existing session
        
        Args:
            session_dir: Path to session directory
            
        Returns:
            Loaded SessionMetadata
        """
        self.session_dir = session_dir
        manifest_path = session_dir / "manifest.json"
        
        if not manifest_path.exists():
            raise FileNotFoundError(f"No manifest.json found in {session_dir}")
        
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        self.current_session = SessionMetadata(**data)
        return self.current_session
    
    def add_execution_result(
        self,
        user_prompt: str,
        ai_model_used: str,
        script_path: Path,
        status: str,
        mesh_path: Optional[Path] = None,
        error_log: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> ExecutionResult:
        """
        Add an execution result to the session history
        
        Args:
            user_prompt: Original user input
            ai_model_used: "gemini-2.0-flash" or "qwen-2.5-local"
            script_path: Path to generated script
            status: "SUCCESS", "FAILURE", or "CRASH"
            mesh_path: Path to output mesh (if successful)
            error_log: Error message (if failed)
            execution_time_ms: Execution time in milliseconds
            
        Returns:
            The created ExecutionResult
        """
        if not self.current_session:
            raise RuntimeError("No active session")
        
        result = ExecutionResult(
            id=len(self.current_session.history) + 1,
            timestamp=datetime.now().strftime("%H:%M:%S"),
            user_prompt=user_prompt,
            ai_model_used=ai_model_used,
            script_path=str(script_path),
            status=status,
            mesh_path=str(mesh_path) if mesh_path else None,
            error_log=error_log,
            execution_time_ms=execution_time_ms
        )
        
        self.current_session.history.append(result.model_dump())
        self._save_manifest()
        
        return result
    
    def get_latest_mesh(self) -> Optional[Path]:
        """
        Get the path to the most recent successful mesh
        
        Returns:
            Path to latest mesh, or None if no successful executions
        """
        if not self.current_session:
            return None
        
        # Search history in reverse for last successful execution
        for entry in reversed(self.current_session.history):
            if entry.get("status") == "SUCCESS" and entry.get("mesh_path"):
                mesh_path = Path(entry["mesh_path"])
                if mesh_path.exists():
                    return mesh_path
        
        return None
    
    def get_script_path(self, execution_id: int) -> Path:
        """
        Get path for a generated script
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Path where script should be saved
        """
        if not self.session_dir:
            raise RuntimeError("No active session")
        
        return self.session_dir / "scripts" / f"gen_{execution_id:03d}.py"
    
    def get_mesh_path(self, execution_id: int) -> Path:
        """
        Get path for an output mesh
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Path where mesh should be saved
        """
        if not self.session_dir:
            raise RuntimeError("No active session")
        
        return self.session_dir / "meshes" / f"{execution_id:03d}.stl"
    
    def _save_manifest(self):
        """Save current session metadata to manifest.json"""
        if not self.session_dir or not self.current_session:
            return
        
        manifest_path = self.session_dir / "manifest.json"
        
        with open(manifest_path, 'w') as f:
            json.dump(
                self.current_session.model_dump(),
                f,
                indent=2
            )
