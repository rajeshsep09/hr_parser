from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sys
import os

# Add src directory to Python path
current_file_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_file_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from hr_parser import hr_parser_router
from hr_parser.scoring_router import router as scoring_router

app = FastAPI(title="HR Parser Demo", version="0.1.0")

# Get the directory of this file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

# Include API routers
app.include_router(hr_parser_router, prefix="/hr")
app.include_router(scoring_router, prefix="/hr")

@app.get("/")
def read_root():
    """Serve the main upload interface."""
    return FileResponse(os.path.join(current_dir, "static", "index.html"))

@app.get("/health")
def health():
    return {"ok": True}