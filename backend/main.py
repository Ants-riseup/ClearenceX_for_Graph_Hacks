"""ClearanceX API. Data routes fail closed on authentication/storage failures."""
import asyncio
import logging
import re
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from database.connection import SessionLocal, init_db
from context_app import models
from context_app.config import ORIGINS, MAX_REQUEST_BYTES, SECURE_COOKIES
from context_app.security import identity, check_csrf, authorize_dossier, router as auth_router
from context_app.service import sync_one, reconcile_graph_projections
from context_app.router import router as context_router
from api.routes import router
from context_app.upload import router as upload_router, process_one_upload
from context_app.workspace import router as workspace_router
from context_app.exports import router as export_router

logger = logging.getLogger(__name__)


class BodyLimitMiddleware:
    """Bound actual bytes too, including chunked requests without Content-Length."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        limit = MAX_REQUEST_BYTES if path == "/api/upload" or path.endswith("/replacement") else 64 * 1024
        used = 0
        async def limited_receive():
            nonlocal used
            message = await receive()
            used += len(message.get("body", b""))
            if used > limit:
                raise HTTPException(413, "Request body exceeds the allowed size.")
            return message
        headers = dict(scope.get("headers", []))
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse({"detail": "Invalid content length."}, status_code=400)(scope, receive, send)
        if declared > limit:
            return await JSONResponse({"detail": "Request body exceeds the allowed size."}, status_code=413)(scope, receive, send)
        await self.app(scope, limited_receive, send)


async def projection_loop():
    while True:
        try:
            await asyncio.to_thread(sync_one)
        except Exception:
            logger.exception("Graph worker could not access its durable queue")
        await asyncio.sleep(1)


async def ingestion_loop():
    while True:
        try:
            await asyncio.to_thread(process_one_upload)
        except Exception:
            logger.exception("Ingestion worker failed")
        await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(app):
    init_db()
    await asyncio.to_thread(reconcile_graph_projections)
    with SessionLocal() as db:
        db.query(models.AgentRun).filter(models.AgentRun.status == "running", models.AgentRun.updated_at < int(time.time()) - 120).update(
            {"status": "failed", "result": {"error": "Investigation interrupted. Start a new run."}})
        db.commit()
    worker = asyncio.create_task(projection_loop())
    ingestion = asyncio.create_task(ingestion_loop())
    yield
    worker.cancel()
    ingestion.cancel()
    try:
        await worker
    except asyncio.CancelledError:
        pass
    try:
        await ingestion
    except asyncio.CancelledError:
        pass


app = FastAPI(title="ClearanceX Context Agent", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=sorted(ORIGINS), allow_credentials=True,
    allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-CSRF-Token"])


@app.middleware("http")
async def protect(request: Request, call_next):
    try:
        if int(request.headers.get("content-length", "0")) > MAX_REQUEST_BYTES:
            raise HTTPException(413, "Request exceeds the 80 MB limit.")
        path = request.url.path
        if path.startswith("/uploads"):
            raise HTTPException(404, "Use authorized document access.")
        if path.startswith("/api/") and not path.startswith("/api/auth/") and request.method != "OPTIONS":
            user = await asyncio.to_thread(identity, request)
            request.state.user = user
            if request.method not in {"GET", "HEAD"}:
                check_csrf(request, user)
                if user["role"] not in {"reviewer", "admin"}:
                    raise HTTPException(403, "Reviewer permission required.")
            match = re.match(r"^/api/(?:shipments|upload)/([^/]+)", path)
            if match and match[1] != "upload":
                with SessionLocal() as db:
                    authorize_dossier(db, match[1], user)
        response = await call_next(request)
    except HTTPException as exc:
        response = JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    except Exception:
        logger.exception("Request failed")
        response = JSONResponse({"detail": "Service temporarily unavailable."}, status_code=503)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    if SECURE_COOKIES:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


app.include_router(auth_router)
app.include_router(context_router)
app.include_router(workspace_router)
app.include_router(export_router)
app.include_router(router)
app.include_router(upload_router)
app.add_middleware(BodyLimitMiddleware)


@app.get("/health/live")
@app.get("/health")
def live():
    return {"status": "ok", "service": "clearancex", "version": "0.2.0"}


@app.get("/health/ready")
def ready():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        from context_app.graph import GraphRepository
        GraphRepository("health").client.connection.ping()
    except Exception:
        return JSONResponse({"status": "unavailable"}, status_code=503)
    return {"status": "ready"}

