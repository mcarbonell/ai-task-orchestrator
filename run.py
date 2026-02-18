#!/usr/bin/env python3
"""
AI Task Orchestrator - Launcher
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from cli import cli

if __name__ == '__main__':
    cli()
