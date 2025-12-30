"""
LumenOrb v2.0 - Safe Execution Module
Isolates PicoGK execution in subprocess to prevent C++ segfaults from crashing the GUI
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class ExecutionEngine:
    """
    Manages safe execution of generated PicoGK scripts
    Uses subprocess isolation to catch C++ crashes
    """
    
    def __init__(self, max_timeout_seconds: int = 30):
        self.max_timeout = max_timeout_seconds
    
    def execute_safe(self, script_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Execute a PicoGK script in an isolated subprocess
        
        Args:
            script_path: Path to the generated Python script
            output_dir: Directory for output files
            
        Returns:
            Dictionary with status, error info, and execution time
        """
        start_time = datetime.now()
        
        try:
            # Run script in isolated process
            proc = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=self.max_timeout,
                cwd=str(output_dir)  # Set working directory for output files
            )
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Check for various failure modes
            if proc.returncode == 0:
                return {
                    "status": "SUCCESS",
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "execution_time_ms": execution_time
                }
            
            # Windows Access Violation (C++ crash)
            if proc.returncode == 3221225477 or proc.returncode == -1073741819:
                return {
                    "status": "CRASH",
                    "reason": "PicoGK Memory Violation - Possible voxel explosion or invalid geometry",
                    "stderr": proc.stderr,
                    "execution_time_ms": execution_time
                }
            
            # Check for specific error patterns
            if "Access Violation" in proc.stderr or "Segmentation fault" in proc.stderr:
                return {
                    "status": "CRASH",
                    "reason": "C++ Runtime Error in PicoGK",
                    "stderr": proc.stderr,
                    "execution_time_ms": execution_time
                }
            
            # Generic Python error
            return {
                "status": "ERROR",
                "trace": proc.stderr,
                "stdout": proc.stdout,
                "execution_time_ms": execution_time
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "ERROR",
                "reason": f"Execution exceeded {self.max_timeout}s timeout - possible infinite loop",
                "trace": "TIMEOUT"
            }
        
        except Exception as e:
            return {
                "status": "ERROR",
                "reason": f"Execution engine error: {str(e)}",
                "trace": str(e)
            }
    
    def validate_output(self, output_dir: Path, expected_filename: str = "output.stl") -> bool:
        """
        Check if the expected output file was created
        
        Args:
            output_dir: Directory to check
            expected_filename: Name of expected output file
            
        Returns:
            True if file exists and is non-empty
        """
        output_file = output_dir / expected_filename
        
        if not output_file.exists():
            return False
        
        # Check file is not empty (STL files should be at least a few KB)
        if output_file.stat().st_size < 100:
            return False
        
        return True
    
    def extract_error_context(self, stderr: str) -> str:
        """
        Parse Python traceback to extract meaningful error message
        
        Args:
            stderr: Standard error output from subprocess
            
        Returns:
            Cleaned error message for AI feedback
        """
        lines = stderr.strip().split('\n')
        
        # Find the actual error line (usually last line)
        if lines:
            error_line = lines[-1]
            
            # Extract traceback context (last few lines)
            if len(lines) > 3:
                context = '\n'.join(lines[-4:])
                return context
            
            return error_line
        
        return "Unknown error - no stderr output"
