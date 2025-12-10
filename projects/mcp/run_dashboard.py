#!/usr/bin/env python3
"""
Simple dashboard runner without Unicode characters for Windows compatibility.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the dashboard with minimal output."""
    print("Traffic-Restaurant Dashboard")
    print("=" * 40)
    
    # Check if app exists
    app_file = Path("dashboard/app.py")
    if not app_file.exists():
        print("[ERROR] dashboard/app.py not found")
        return False
    
    print("Starting dashboard...")
    print("Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        # Start the dashboard
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "dashboard.app:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\nDashboard stopped")
    except Exception as e:
        print(f"[ERROR] Failed to start: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("Press Enter to exit...")
    sys.exit(0 if success else 1)