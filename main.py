"""
Root entry point for Render deployment.
Delegates to backend/main.py via uvicorn.
"""
import os
import sys
import uvicorn

# Ensure backend/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)