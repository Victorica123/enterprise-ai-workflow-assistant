"""应用装配：CORS、lifespan 初始化、路由注册。

业务端点在 app.routes.* 中，按领域拆分；重量级初始化（建库、建表、
模型预热）在 lifespan 中执行，import 本模块不再产生副作用。
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_default_answer_mode, get_llm_settings, get_retriever_mode, load_local_env
from app.database import get_embedding_stats, init_db
from app.embeddings import warm_up_embeddings
from app.graph_store import init_graph_store
from app.llm import is_llm_configured
from app.logging_config import setup_logging
from app.models import SystemStatus
from app.rag import list_documents
from app.routes.chat import router as chat_router
from app.routes.documents import router as documents_router
from app.routes.embedding_admin import router as embedding_router
from app.routes.graph import router as graph_router
from app.routes.observability import router as observability_router
from app.routes.tickets import router as tickets_router
from app.status_service import build_embedding_status
from app.tools import init_tools


logger = logging.getLogger(__name__)

load_local_env()
setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    init_tools()
    init_graph_store()
    # A3: 启动时预加载真实 embedding 模型（不可用时为空操作），
    # 避免第一个 /chat 请求承担秒级模型加载延迟。
    warm_up_embeddings()
    logger.info("api_started")
    yield


app = FastAPI(
    title="Enterprise AI Workflow Assistant API",
    description="V5 knowledge QA + agentic RAG + tickets + tools + GraphRAG + observability.",
    version="0.5.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


for feature_router in (
    documents_router,
    chat_router,
    embedding_router,
    observability_router,
    graph_router,
    tickets_router,
):
    app.include_router(feature_router)


# ---------------------------------------------------------------------------
# 健康检查 & 系统状态
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/system/status", response_model=SystemStatus)
def get_system_status() -> SystemStatus:
    documents = list_documents()
    embedding = build_embedding_status(get_embedding_stats())
    llm_settings = get_llm_settings()
    return SystemStatus(
        status="ok",
        document_count=len(documents),
        chunk_count=embedding.total_chunks,
        llm_provider=llm_settings.provider,
        llm_configured=is_llm_configured(),
        default_answer_mode=get_default_answer_mode(),
        default_retriever_mode=get_retriever_mode(),
        embedding=embedding,
    )
