from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from loguru import logger
import sys
from pathlib import Path

sys.path.append('/app')

from webapp.api.routes import router

logger.add(
    "logs/webapp.log",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
)

app = FastAPI(
    title="Transaction Manager API",
    description="API для управления транзакциями через Telegram Mini App",
    version="1.0.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "webapp" / "static"

# Создаем директорию если не существует
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Монтируем статические файлы с правильным путем
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(router)


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path(BASE_DIR / "static" / "index.html")
    if html_path.exists():
        return FileResponse(html_path)
    return HTMLResponse(content="<h1>File not found</h1>", status_code=404)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Transaction Manager API",
        "version": "1.0.1"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error",
        }
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
