"""Configuration for the parser module."""

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Input file path
INPUT_FILE = PROJECT_ROOT / "docs" / "CVs enviados.txt"

# Output file path
OUTPUT_FILE = PROJECT_ROOT / "src" / "frontend" / "data.json"
