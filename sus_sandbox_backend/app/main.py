from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routers.sus import router as sus_router

app = FastAPI(title="SUS Sandbox Backend", version="0.2.0")

# Pastas locais (sandbox)
BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Expor arquivos anexados (evidências)
app.mount("/sus/files", StaticFiles(directory=str(UPLOADS_DIR)), name="sus-files")

app.include_router(sus_router, prefix="/sus", tags=["SUS"])
