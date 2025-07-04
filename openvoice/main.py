"""
Main entrypoint for the OpenVoice FastAPI application.
This module can be executed using: python -m openvoice.main
"""

import sys
import os

# Add the current directory to the Python path to ensure proper imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from openvoice.openvoice_server import app

def main():
    """Main function to start the FastAPI server."""
    import uvicorn
    print("Starting OpenVoice FastAPI server...")
    print("Server will be available at: http://0.0.0.0:8000")
    print("API documentation available at: http://0.0.0.0:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main() 