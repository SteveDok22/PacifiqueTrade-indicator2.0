"""
PacifiqueTrade Indicator 2.0 - Main Entry Point

This is the main entry point for the trading indicator system.
Run this file to start the indicator in scheduled mode.
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import Config, config
from core.exceptions import PacifiqueTradeError, ConfigurationError


# ASCII Art Logo
LOGO = r"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██████╗  █████╗  ██████╗██╗███████╗██╗ ██████╗ ██╗   ██╗███████╗║
║   ██╔══██╗██╔══██╗██╔════╝██║██╔════╝██║██╔═══██╗██║   ██║██╔════╝║
║   ██████╔╝███████║██║     ██║█████╗  ██║██║   ██║██║   ██║█████╗  ║
║   ██╔═══╝ ██╔══██║██║     ██║██╔══╝  ██║██║▄▄ ██║██║   ██║██╔══╝  ║
║   ██║     ██║  ██║╚██████╗██║██║     ██║╚██████╔╝╚██████╔╝███████╗║
║   ╚═╝     ╚═╝  ╚═╝ ╚═════╝╚═╝╚═╝     ╚═╝ ╚══▀▀═╝  ╚═════╝ ╚══════╝║
║                                                           ║
║             T R A D E   I N D I C A T O R   2.0           ║
║                                                           ║
║                                                           ║
║               Built by Stiven | Version 2.0.0             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""

