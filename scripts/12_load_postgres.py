"""PostgreSQL / Supabase Database Loader Entrypoint.

Delegates execution to scripts.12_load_supabase.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.12_load_supabase import main

if __name__ == "__main__":
    sys.exit(main())
