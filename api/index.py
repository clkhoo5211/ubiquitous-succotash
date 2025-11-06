"""Vercel Serverless Entry Point

This file is required for Vercel deployment.
It wraps the FastAPI app with Mangum to make it compatible with AWS Lambda/Vercel.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Patch the get_db function to use serverless-compatible version
import src.core.database as db_module
from src.core.serverless import get_serverless_db
db_module.get_db = get_serverless_db

from mangum import Mangum
from src.main import app

# Wrap FastAPI app with Mangum for serverless compatibility
# lifespan="off" because Vercel doesn't support startup/shutdown events
handler = Mangum(app, lifespan="off")

# Expose app for debugging
__all__ = ["handler", "app"]

