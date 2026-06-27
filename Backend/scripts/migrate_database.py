#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.database import connect_database, ensure_schema, settings_from_environment


def main() -> None:
    data_dir = Path(os.environ.get("XNP_DATA_DIR", ".xnp-data")).resolve()
    settings = settings_from_environment(data_dir)
    with connect_database(settings) as db:
        ensure_schema(db)
    print(f"database schema ready: {settings.backend}")


if __name__ == "__main__":
    main()
