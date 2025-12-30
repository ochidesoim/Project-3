"""
LumenOrb v2.0 - Template Engine
Renders Jinja2 templates with validated parameters
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from typing import Dict, Any

from src.core.models import GeometryRequest


class TemplateEngine:
    """
    Manages Jinja2 template rendering for PicoGK scripts
    """
    
    def __init__(self, template_dir: Path):
        """
        Initialize the template engine
        
        Args:
            template_dir: Directory containing .jinja template files
        """
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def render(self, request: GeometryRequest, output_path: Path) -> Path:
        """
        Render a template with validated parameters
        
        Args:
            request: Validated GeometryRequest from AI
            output_path: Path where rendered script should be saved
            
        Returns:
            Path to the rendered script file
        """
        # Validate parameters against schema
        validated_params = request.get_validated_params()
        
        # Load template
        template_name = f"{request.template_id}.py.jinja"
        template = self.env.get_template(template_name)
        
        # Render with validated parameters
        rendered_code = template.render(
            params=validated_params.model_dump(),
            intent=request.intent
        )
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered_code, encoding='utf-8')
        
        return output_path
    
    def list_available_templates(self) -> list[str]:
        """
        Get list of available template IDs
        
        Returns:
            List of template IDs (without .py.jinja extension)
        """
        templates = []
        for file in self.template_dir.glob("*.py.jinja"):
            template_id = file.stem.replace('.py', '')
            templates.append(template_id)
        return templates
