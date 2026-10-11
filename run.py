"""
SolSpot Application Launcher.
Runs the FastAPI server with uvicorn.
"""
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"[SolSpot] Starting server at http://localhost:{port} ...")
    uvicorn.run("backend.app:app", host="0.0.0.0", port=port, reload=True)
