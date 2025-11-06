"""Minimal test handler to verify Vercel Python runtime works"""

def handler(event, context):
    """Minimal test - no dependencies"""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": """
        <!DOCTYPE html>
        <html>
        <head><title>Vercel Test</title></head>
        <body style="font-family: Arial; padding: 40px; background: #0a0a0a; color: #00ff00;">
            <h1>✅ Vercel Python Runtime Works!</h1>
            <p>If you see this, the basic Lambda function is working.</p>
            <p>Next: Check if imports work...</p>
        </body>
        </html>
        """
    }

