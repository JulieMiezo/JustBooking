import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

BASE_DIR = os.path.dirname(__file__)

from database import engine, Base
from routers import auth, clients, admin, upload

# 建立所有資料表
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="JustBooking 客戶建置系統",
    description="客戶申請與後台管理 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(auth.router,    prefix="/api/auth",    tags=["認證"])
app.include_router(clients.router, prefix="/api/clients", tags=["客戶申請"])
app.include_router(admin.router,   prefix="/api/admin",   tags=["後台管理"])
app.include_router(upload.router,  prefix="/api/upload",  tags=["檔案上傳"])

# 靜態檔案
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

NO_CACHE = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"}

@app.get("/")
def serve_client():
    return FileResponse(os.path.join(BASE_DIR, "static/client.html"), headers=NO_CACHE)

@app.get("/admin")
def serve_admin():
    return FileResponse(os.path.join(BASE_DIR, "static/admin.html"), headers=NO_CACHE)

@app.get("/health")
def health_check():
    return {"status": "ok"}
