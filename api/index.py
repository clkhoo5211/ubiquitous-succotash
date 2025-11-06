"""Vercel Serverless Entry Point with Error Handling

This file is required for Vercel deployment.
It wraps the FastAPI app with Mangum to make it compatible with AWS Lambda/Vercel.
"""

import os
import sys
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def handler(event, context):
    """Lambda handler with comprehensive error catching"""
    try:
        # Try to import and patch database
        import src.core.database as db_module
        from src.core.serverless import get_serverless_db
        db_module.get_db = get_serverless_db
        
        # Import Mangum and app
        from mangum import Mangum
        from src.main import app
        
        # Create Mangum handler
        mangum_handler = Mangum(app, lifespan="off")
        
        # Call the actual handler
        return mangum_handler(event, context)
        
    except Exception as e:
        # Catch and return detailed error
        error_trace = traceback.format_exc()
        print(f"ERROR: {str(e)}")
        print(f"TRACEBACK:\n{error_trace}")
        
        # Return HTML error page with full traceback
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "text/html"},
            "body": f"""
            <!DOCTYPE html>
            <html>
            <head><title>Deployment Error</title></head>
            <body style="font-family: monospace; padding: 20px; background: #1a1a1a; color: #00ff00;">
                <h1 style="color: #ff0000;">🚫 Deployment Error</h1>
                <h2>Error Message:</h2>
                <pre style="background: #000; padding: 15px; border-radius: 5px; overflow-x: auto;">{str(e)}</pre>
                <h2>Full Traceback:</h2>
                <pre style="background: #000; padding: 15px; border-radius: 5px; overflow-x: auto;">{error_trace}</pre>
                <hr>
                <p>Event: <code>{event}</code></p>
                <p>Python Version: {sys.version}</p>
                <p>Python Path: {sys.path}</p>
            </body>
            </html>
            """
        }

# Expose for debugging
__all__ = ["handler"]
