from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    for name, loader in (
        ("BM25S", lambda: __import__("retrieval.bm25_index", fromlist=["load_bm25"]).load_bm25()),
        ("TurboVec", lambda: __import__("retrieval.turbovec_index", fromlist=["load_turbovec"]).load_turbovec()),
    ):
        try:
            loader()
            logger.info(f"{name} index loaded")
        except Exception as e:
            logger.warning(f"{name} index not loaded: {e}")
    try:
        from graph.taric_tree import load_taric_graph
        await load_taric_graph()
        logger.info("TARIC graph loaded")
    except Exception as e:
        logger.warning(f"TARIC graph not loaded: {e}")
    yield


app = FastAPI(title="TARIC HS10 Classifier", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.classifier import router as classifier_router  # noqa: E402
app.include_router(classifier_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
