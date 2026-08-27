from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.bootstrap import init_db_and_admin
from app.config import settings
from app.routers import auth, ingest, sites, web, weighings

app = FastAPI(title="BARON IN-OUT Cloud Portal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db_and_admin()


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(sites.router, prefix="/api/sites", tags=["sites"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
app.include_router(weighings.router, prefix="/api/weighings", tags=["weighings"])
app.include_router(web.router, tags=["web"])

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
