"""DSAapp Root Backend Runner.

Standard entrypoint to launch DSAapp FastAPI server from repository root.
"""
import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    reload = os.environ.get("RELOAD", "false").lower() in ("true", "1")
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=reload)
