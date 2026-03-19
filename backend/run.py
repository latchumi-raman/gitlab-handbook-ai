"""
Development server entry point.
Run this file directly: python run.py
"""

import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host    = os.getenv("API_HOST", "0.0.0.0"),
        port    = int(os.getenv("API_PORT", 8000)),
        reload  = True,        # auto-reload on file save — only for dev
        log_level = "info",
    )