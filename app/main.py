from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.command_routes import router as command_router
from app.api.match_routes import router as match_router
from app.api.query_routes import router as query_router
from app.api.system_routes import router as system_router
from app.api.ws_routes import router as ws_router
from app.container import build_container

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)


def _allowed_origins() -> list[str]:
    raw = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173')
    return [x.strip() for x in raw.split(',') if x.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = build_container()
    try:
        yield
    finally:
        await app.state.container.tick_loop.shutdown()


app = FastAPI(title="Realtime Xiangqi", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware('http')
async def request_log_middleware(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception('http request failed path=%s method=%s', request.url.path, request.method)
        raise
    dur_ms = int((time.time() - start) * 1000)
    logger.info('http request path=%s method=%s status=%s dur_ms=%s', request.url.path, request.method, response.status_code, dur_ms)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception('unhandled exception: %s', exc)
    return JSONResponse(status_code=500, content={"detail": "internal server error"})


app.include_router(system_router)
app.include_router(match_router)
app.include_router(command_router)
app.include_router(query_router)
app.include_router(ws_router)
