#!/usr/bin/env python
"""
Simple script to start the vehicle detection server.
Run this from the project root directory.
"""
import subprocess
import sys
from pathlib import Path

def main():
    backend_dir = Path(__file__).parent / "backend"
    
    if not backend_dir.exists():
        print("Error: backend directory not found!")
        sys.exit(1)
    
    print("🚀 Starting Vehicle Detection Server...")
    print("📍 Backend directory:", backend_dir)
    print("🌐 Server will be available at: http://localhost:8000")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=str(backend_dir),
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

