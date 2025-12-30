"""
Noyron Architecture - Midnight Stealth Dashboard
------------------------------------------------
Cyberpunk Engineering Console.
Layout: 3-Column Bento Grid (Left: Input/Params, Center: Pipeline, Right: Render)
"""

import warnings
warnings.simplefilter("ignore")  # Suppress deprecation warnings (e.g. Google GenAI)

import sys
import time
import json
import random
from pathlib import Path
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich import box

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.agent import Agent
from src.core.compiler import AtomicCompiler

# --- PALETTE (Midnight Stealth) ---
C_BG = "grey7"             # Deep Obsidian
C_BORDER = "grey30"        # Matte Steel
C_TEXT_MAIN = "grey85"     # Soft White
C_TEXT_DIM = "grey50"      # Muted Text
C_ACCENT_USER = "spring_green3" # Muted Emerald (User Data)
C_ACCENT_SYS = "slate_blue3"    # Soft Indigo (System Data/Structure)
C_WARN = "orange3"

console = Console()

class NoyronDashboard:
    def __init__(self):
        self.layout = Layout()
        self.agent = None
        self.compiler = None
        self.last_command = "..."
        self.last_result = None
        self.logs = []
        
        self.setup_core()
        self.init_layout()

    def setup_core(self):
        try:
            system_prompt = Path("resources/system_prompt.txt")
            cheatsheet = Path("resources/picogk_cheatsheet.md")
            self.agent = Agent(
                system_prompt_path=system_prompt,
                cheatsheet_path=cheatsheet,
                local_model_name="lumenorb-v1:latest"
            )
            self.compiler = AtomicCompiler()
            self.log_msg("System Initialized.", "green")
        except Exception as e:
            self.log_msg(f"Init Error: {e}", "red")

    def log_msg(self, msg, color="white"):
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{color}][{timestamp}] {msg}[/]")
        if len(self.logs) > 20:
            self.logs.pop(0)

    def init_layout(self):
        """
        State Machine Layout:
        [ Header ]
        [ Left (Input/Params) | Center (Pipeline) | Right (Render) ]
        [ Footer ]
        """
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        
        self.layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="center", ratio=1),
            Layout(name="right", ratio=1)
        )
        
        self.layout["left"].split_column(
            Layout(name="cli_input", size=3), # Top Left: CLI Input
            Layout(name="parameters", ratio=1) # Bottom Left: Parameters
        )

    # --- RENDERERS ---

    def render_header(self):
        title = Text("NOYRON", style="bold white")
        sub = Text("ANTIGRAVITY", style=f"bold {C_ACCENT_SYS}")
        return Panel(
            Align.center(Text.assemble(title, " ", sub)),
            style=f"{C_BORDER} on {C_BG}",
            box=box.HEAVY_EDGE
        )

    def render_cli_input(self):
        return Panel(
            Text(f"> {self.last_command}", style=f"bold {C_TEXT_MAIN}"),
            title="[bold]CLI INPUT[/]",
            border_style=C_BORDER,
            style=f"on {C_BG}",
            box=box.ROUNDED
        )

    def render_parameters(self):
        """Bottom Left Panel: Extracted Parameters"""
        table = Table(expand=True, border_style=C_BORDER, box=box.SIMPLE_HEAD, show_header=True)
        table.add_column("Param", style=C_TEXT_DIM)
        table.add_column("Value", style="bold white")
        table.add_column("Src", style="italic")

        if self.last_result and self.last_result.get("mode") == "engineering":
            meta = self.last_result.get("meta", {})
            params = meta.get("extracted_params", {})
            
            if not params:
                 table.add_row("(No Params)", "-", "-")
            
            for k, v in params.items():
                # Heuristic source coloring
                source = "USER" if k in ["thrust", "count", "holes", "radius"] else "SYS"
                color = C_ACCENT_USER if source == "USER" else C_ACCENT_SYS
                table.add_row(k, str(v), f"[{color}]{source}[/]")
        elif self.last_result:
            table.add_row("Mode", self.last_result.get("mode", "unknown"), "[grey50]AUTO[/]")
        else:
            table.add_row("--", "--", "--")

        return Panel(
            table,
            title=f"[{C_ACCENT_USER}]PARAMETERS[/]",
            border_style=C_BORDER,
            style=f"on {C_BG}",
            box=box.ROUNDED
        )

    def render_pipeline(self):
        """Center Panel: Node Tree"""
        root = Tree("ROOT", style=C_TEXT_DIM, guide_style=C_BORDER)
        
        if self.last_result:
            mode = self.last_result.get("mode", "unknown").upper()
            intent = self.last_result.get("intent", "Command")
            
            main_node = root.add(f"[{C_ACCENT_SYS}]MODE: {mode}[/]")
            
            ops = self.last_result.get("operations", [])
            if not ops:
                main_node.add("[italic]No operations[/]")
            
            # Limit tree size for UI
            display_ops = ops[:12] 
            
            for op in display_ops:
                pid = op.get("id", "?")
                otype = op.get("op", "?")
                pnode = main_node.add(f"[white]{pid}[/] ([{C_ACCENT_SYS}]{otype}[/])")
                
                # Show key detail if exists
                params = op.get("params", {})
                if 'z' in params:
                    pnode.add(f"Z: {params['z']:.1f}")
            
            if len(ops) > 12:
                main_node.add(f"[italic]...and {len(ops)-12} more[/]")
                
        else:
            root.add("[italic dim]Idle[/]")

        return Panel(
            root,
            title="[bold]PIPELINE[/]",
            border_style=C_BORDER,
            style=f"on {C_BG}",
            box=box.ROUNDED
        )

    def render_render_panel(self):
        """Right Panel: Wireframe Placeholder / Logs"""
        # "Render" in CLI is abstract -> We show the Build Logs / ASCII status
        
        layout = Layout()
        layout.split_column(
            Layout(name="status", ratio=1),
            Layout(name="sys_logs", ratio=1)
        )
        
        # Status "Wireframe"
        status_text = Align.center(
            Text("\n[ WIREFRAME VIEW ]\n\n(PicoGK Viewer Running)\n\n   /\\\n  /  \\\n |    |\n |____|", style=C_TEXT_DIM), 
            vertical="middle"
        )
        
        log_text = "\n".join(self.logs)
        
        return Panel(
            log_text,
            title="[bold]RENDER / SYSTEM LOGS[/]",
            border_style=C_BORDER,
            style=f"on {C_BG}",
            box=box.ROUNDED
        )

    def render_footer(self):
        return Panel(
            Align.left(Text(" > Type 'exit' to quit. 'clear' to reset.", style=C_TEXT_DIM)),
            style=f"{C_BORDER} on {C_BG}",
            box=box.HEAVY_EDGE
        )

    # --- LOOP ---

    def update_view(self):
        self.layout["header"].update(self.render_header())
        
        self.layout["cli_input"].update(self.render_cli_input())
        self.layout["parameters"].update(self.render_parameters())
        
        self.layout["center"].update(self.render_pipeline())
        
        self.layout["right"].update(self.render_render_panel())
        
        self.layout["footer"].update(self.render_footer())
        return self.layout

    def run(self):
        console.clear()
        with Live(self.update_view(), refresh_per_second=4, screen=True) as live:
            while True:
                try:
                    # BLOCKING INPUT (Pauses Live Update)
                    live.stop()
                    user_input = console.input(f"[{C_ACCENT_USER}]> [/]")
                    live.start()
                    
                    if user_input.lower() in ["exit", "quit"]:
                        break
                    
                    if not user_input.strip():
                        continue
                        
                    if user_input.lower() == "clear":
                        self.last_result = None
                        self.last_command = "..."
                        self.logs = []
                        live.update(self.update_view())
                        continue

                    # UPDATE STATE
                    self.last_command = user_input
                    self.log_msg(f"Input: {user_input}", "white")
                    live.update(self.update_view()) # Show input immediately
                    
                    # PROCESS
                    self.log_msg("Agent: Thinking...", C_ACCENT_SYS)
                    result = self.agent.solve_problem(user_input)
                    self.last_result = result
                    live.update(self.update_view()) # Show Pipeline/Params
                    
                    # COMPILE
                    mode = result.get("mode", "unknown")
                    if mode == "engineering":
                         self.log_msg("Engineering Mode Active", C_ACCENT_USER)
                    
                    self.log_msg("Compiler: Building...", C_ACCENT_SYS)
                    json_path = self.compiler.compile(result)
                    
                    if json_path:
                        self.log_msg("Build Complete", "green")
                    else:
                        self.log_msg("Build Failed", "red")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.log_msg(f"Crit Error: {e}", "red")

if __name__ == "__main__":
    dashboard = NoyronDashboard()
    dashboard.run()
