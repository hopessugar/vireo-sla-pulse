"""
Vireo SLA Pulse — Entry Point
Single command to start: python run.py
"""
import os
import sys
import uvicorn

def main():
    # Set data directory
    data_dir = os.path.dirname(os.path.abspath(__file__))
    os.environ['DATA_DIR'] = data_dir
    
    print("=" * 60)
    print("  Vireo SLA Pulse -- First-Response Breach Intelligence")
    print("=" * 60)
    print(f"  Data directory: {data_dir}")
    print(f"  Dashboard: http://localhost:8000")
    print(f"  API docs:  http://localhost:8000/docs")
    print("=" * 60)
    print()
    
    # Run the FastAPI server
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )

if __name__ == "__main__":
    main()
