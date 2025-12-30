# LumenOrb v2.0

**Agentic Computational Engineering Environment**

> "Physics over Pixels" - Natural language to physically valid voxel geometry

## Overview

LumenOrb is a revolutionary CAD environment that transpiles natural language into executable PicoGK scripts for generating complex voxel-based geometry. It bypasses traditional B-Rep/NURBS constraints by utilizing Code Representations and Signed Distance Fields.

## Architecture Highlights

### v2.0 Paradigm Shift
- **AI as Parameter Extractor**: The AI no longer writes code—it extracts parameters from natural language
- **Template-Based Generation**: Pre-validated Jinja2 templates ensure crash-free execution
- **Subprocess Isolation**: PicoGK C++ crashes cannot kill the GUI
- **Type-Safe Validation**: Pydantic models enforce physical constraints

### Tech Stack
- **GUI**: PyQt6 with "Darkroom" aesthetic (#0A0A0A)
- **Geometry Kernel**: PicoGK (Voxel/SDF operations)
- **Visualization**: PyVista (GPU-accelerated OpenGL)
- **AI**: Gemini 2.0 Flash (cloud) + Qwen 2.5 (local)
- **Templates**: Jinja2 with validated parameters

## Installation

### Prerequisites
- Python 3.10+
- Windows 11 (required for PicoGK DLL compatibility)
- 16-core CPU (recommended)
- RTX 4060 or equivalent GPU

### Setup

1. **Clone and navigate:**
```bash
cd "D:\Project 3"
```

2. **Create virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
copy .env.template .env
# Edit .env and add your GEMINI_API_KEY
```

5. **Install PicoGK (Critical):**
```bash
# Follow official PicoGK Windows installation guide
# https://github.com/leap71/PicoGK
# Ensure DLLs are in PATH or project directory
```

## Usage

### Launch Application
```bash
python main.py
```

### Example Commands
```
> Create a cylinder, 50mm radius, 100mm height
> Make a fuel tank with 2mm walls and gyroid infill
> Create a hollow sphere, 30mm diameter, 1mm shell
```

### Special Commands
- `clear` / `reset` - Clear conversation history
- `exit` / `quit` - Close application

## Project Structure

```
LumenOrb/
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── .env.template                    # Environment config
├── resources/
│   ├── system_prompt.txt            # AI instructions
│   ├── picogk_cheatsheet.md         # API reference
│   └── theme.qss                    # Darkroom stylesheet
├── src/
│   ├── core/
│   │   ├── models.py                # Pydantic schemas
│   │   ├── agent.py                 # AI parameter extraction
│   │   ├── template_engine.py       # Jinja2 rendering
│   │   ├── execution.py             # Subprocess isolation
│   │   └── session.py               # Session management
│   ├── ui/
│   │   ├── main_window.py           # Bento grid layout
│   │   ├── console_widget.py        # Command input
│   │   ├── log_widget.py            # Log stream
│   │   └── viewport.py              # PyVista 3D view
│   └── computational/
│       └── templates/
│           ├── base_cylinder.py.jinja
│           └── shell_lattice_gyroid.py.jinja
└── output/
    └── session_YYYYMMDD_HHMM/
        ├── manifest.json            # Session metadata
        ├── scripts/                 # Generated Python
        └── meshes/                  # Output STL files
```

## Available Templates

### 1. `base_cylinder`
Solid cylindrical volume
- Parameters: `radius_mm`, `height_mm`, `voxel_size_mm`

### 2. `shell_lattice_gyroid`
Hollow shell with gyroid infill
- Parameters: `outer_radius_mm`, `wall_thickness_mm`, `lattice_period_mm`, `lattice_thickness_mm`

### 3. `boolean_cut` (Coming Soon)
Boolean subtraction on existing geometry

### 4. `gyroid_infill` (Coming Soon)
Pure gyroid lattice structure

## Safety Features

- **Timeout Protection**: 30s max execution time
- **Voxel Resolution Limits**: Prevents RAM overflow
- **Type Validation**: Pydantic enforces physical constraints
- **Crash Isolation**: C++ segfaults caught in subprocess

## Troubleshooting

### "PicoGK not installed"
- Verify PicoGK DLLs are in PATH
- Check Python version compatibility (3.10+)
- Ensure Windows C++ build tools installed

### "PyVista not available"
```bash
pip install pyvista pyvistaqt
```

### GPU not detected
- Install latest NVIDIA drivers
- Verify CUDA compatibility

## Roadmap

### Phase 2 (Current)
- [x] Template engine
- [x] Base cylinder template
- [x] Shell/gyroid template
- [ ] Boolean operations template
- [ ] True gyroid SDF implementation

### Phase 3 (Future)
- [ ] Cloud compute offloading
- [ ] Multi-user collaboration
- [ ] Direct G-code export
- [ ] Advanced lattice structures

## License

Proprietary - LumenOrb v2.0

## Credits

Built with:
- [PicoGK](https://github.com/leap71/PicoGK) - Computational geometry kernel
- [PyVista](https://pyvista.org/) - 3D visualization
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [Google Gemini](https://deepmind.google/technologies/gemini/) - AI reasoning

---

**"Physics over Pixels"** - LumenOrb Team
