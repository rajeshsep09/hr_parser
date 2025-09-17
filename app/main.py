from fastapi import FastAPI
from hr_parser import hr_parser_router

app = FastAPI(title="HR Parser Demo", version="0.1.0")
app.include_router(hr_parser_router, prefix="/hr")

@app.get("/health")
def health():
    return {"ok": True}