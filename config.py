"""
Polynomial Studio — Configuration
"""
import os
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# All output directories inside the project
RENDER_DIR = os.path.join(BASE_DIR, "renders")
VIDEO_DIR = os.path.join(RENDER_DIR, "videos")
PREVIEW_DIR = os.path.join(RENDER_DIR, "previews")
SCENE_DIR = os.path.join(BASE_DIR, "manim_scenes")
# Temp directory for generated scenes — outside the project tree so
# Flask's watchdog reloader doesn't detect new files and restart the server.
SCENE_TEMP_DIR = tempfile.mkdtemp(prefix="poly_studio_scenes_")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Ensure directories exist
for d in [RENDER_DIR, VIDEO_DIR, PREVIEW_DIR, SCENE_DIR, LOG_DIR]:
    os.makedirs(d, exist_ok=True)

# Flask
SECRET_KEY = os.environ.get("POLYNOMIAL_STUDIO_SECRET", "poly-studio-dev-key-change-in-prod")
DEBUG = os.environ.get("POLYNOMIAL_STUDIO_DEBUG", "0") == "1"

# Rendering
RENDER_TIMEOUT = 300  # seconds
MAX_POLYNOMIALS = 5
MAX_DEGREE = 12

# Python venv fix: clear PYTHONHOME so the venv uses its own stdlib
# correctly instead of picking up wrong stdlib from system Python 3.14.
VENV_DIR = os.path.join(BASE_DIR, ".venv")
PYTHONHOME = ""

# Quality presets: (width, height, fps, quality_flag)
QUALITY_PRESETS = {
    "preview":       {"width": 640,  "height": 360,  "fps": 15, "manim_quality": "-ql",  "label": "Preview"},
    "instagram_45":  {"width": 1080, "height": 1350, "fps": 30, "manim_quality": "-qh",  "label": "Instagram 4:5"},
    "instagram_sq":  {"width": 1080, "height": 1080, "fps": 30, "manim_quality": "-qh",  "label": "Instagram Square"},
    "instagram_reel":{"width": 1080, "height": 1920, "fps": 30, "manim_quality": "-qm",  "label": "Instagram Reel"},
    "youtube":       {"width": 1920, "height": 1080, "fps": 30, "manim_quality": "-qh",  "label": "YouTube"},
    "high":          {"width": 1920, "height": 1080, "fps": 60, "manim_quality": "-qk",  "label": "High Quality"},
}

# Themes: (bg_color, curve_color, accent_color, grid_color, text_color, glow_color)
ANIMATION_THEMES = {
    "neon": {
        "label": "Neon",
        "background": "#0a0a1a",
        "curve_primary": "#00e5ff",
        "curve_secondary": "#e040fb",
        "accent": "#7c4dff",
        "grid": "#1a1a3e",
        "text": "#e0e0e0",
        "root_color": "#ff4081",
        "glow": True,
        "description": "Dark background with cyan/blue curve and purple accents"
    },
    "minimal": {
        "label": "Minimal",
        "background": "#fafafa",
        "curve_primary": "#212121",
        "curve_secondary": "#757575",
        "accent": "#424242",
        "grid": "#e0e0e0",
        "text": "#212121",
        "root_color": "#d32f2f",
        "glow": False,
        "description": "Light background with clean dark axes and elegant curves"
    },
    "aurora": {
        "label": "Aurora",
        "background": "#0d0221",
        "curve_primary": "#00e5ff",
        "curve_secondary": "#d500f9",
        "accent": "#651fff",
        "grid": "#1a0a3e",
        "text": "#cfd8dc",
        "root_color": "#ff6e40",
        "glow": True,
        "description": "Dark atmospheric background with cyan/purple colors"
    },
    "chalkboard": {
        "label": "Chalkboard",
        "background": "#1a2a1a",
        "curve_primary": "#e8e8c8",
        "curve_secondary": "#c8d8c8",
        "accent": "#a8b8a8",
        "grid": "#2a3a2a",
        "text": "#e8e8c8",
        "root_color": "#f0e68c",
        "glow": False,
        "description": "Dark green background with chalk-style mathematical aesthetic"
    },
    "mathematical": {
        "label": "Mathematical",
        "background": "#1a1a2e",
        "curve_primary": "#f5a623",
        "curve_secondary": "#e74c3c",
        "accent": "#3498db",
        "grid": "#2a2a4e",
        "text": "#ecf0f1",
        "root_color": "#2ecc71",
        "glow": False,
        "description": "Dark background with warm mathematical colors"
    },
}
