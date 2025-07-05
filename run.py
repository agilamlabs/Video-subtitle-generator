#!/usr/bin/env python3
"""
Startup script for the Video Subtitle Generator Flask application.
"""

from app import app

if __name__ == '__main__':
    print("Starting Video Subtitle Generator...")
    print("Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    
    
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    ) 