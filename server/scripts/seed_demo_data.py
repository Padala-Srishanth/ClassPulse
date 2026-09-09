"""
scripts/seed_demo_data.py — ClassPulse Demo Data Seeding CLI Wrapper

Allows running:
    python scripts/seed_demo_data.py
from the server directory.
"""

from __future__ import annotations

import os
import sys

# Ensure server root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seed_demo_data import main

if __name__ == "__main__":
    main()
