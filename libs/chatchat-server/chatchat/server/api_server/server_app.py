import argparse
import os
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from chatchat import __version__
from chatchat.settings import Settings
from chatchat.server.api_server.auth_routes import auth_router
from chatchat.server.api_server.chat_routes import chat_router
from chatchat.server.api_server.kb_routes import kb_router
from chatchat.server.api_server.mcp_routes import mcp_router
from chatchat.server.api_server.openai_routes import openai_router
from chatchat.server.api_server.server_routes import server_router
from chatchat.server.api_server.tenant_routes import tenant_router
from chatchat.server.api_server.tool_routes import tool_router
from chatchat.server.chat.completion import completion
from chatchat.server.db.manager import DatabaseManager, db_manager
from chatchat.server.utils import MakeFastAPIOffline


class AppConfig:
    """Configuration for an application instance."""

    def __init__(
        self,
        enable_cors: Optional[bool] = None,
        db: Optional[DatabaseManager] = None,
        title: str = "Langchain-Chatchat API Server",
        run_mode: Optional[str] = None,
    ):
        self.enable_cors = (
            enable_cors
            if enable_cors is not None
            else Settings.basic_settings.OPEN_CROSS_DOMAIN
        )
        self.db = db or db_manager
        self.title = title
        self.run_mode = run_mode


def create_app(config: Optional[AppConfig] = None):
    """Create and configure a FastAPI application instance.

    Args:
        config: Application configuration. Uses defaults from Settings if None.

    Returns:
        Configured FastAPI application ready to serve.
    """
    if config is None:
        config = AppConfig()

    app = FastAPI(title=config.title, version=__version__)
    MakeFastAPIOffline(app)

    if config.enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/", summary="swagger 文档", include_in_schema=False)
    async def document():
        return RedirectResponse(url="/docs")

    app.include_router(auth_router)
    app.include_router(tenant_router)
    app.include_router(chat_router)
    app.include_router(kb_router)
    app.include_router(tool_router)
    app.include_router(openai_router)
    app.include_router(server_router)
    app.include_router(mcp_router)

    app.post(
        "/other/completion",
        tags=["Other"],
        summary="要求llm模型补全(通过LLMChain)",
    )(completion)

    app.mount("/media", StaticFiles(directory=Settings.basic_settings.MEDIA_PATH), name="media")

    img_dir = str(Settings.basic_settings.IMG_DIR)
    app.mount("/img", StaticFiles(directory=img_dir), name="img")

    # Mount Vue 3 frontend (production build, with SPA fallback)
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "static", "frontend")
    frontend_dist = os.path.abspath(frontend_dist)
    if os.path.exists(frontend_dist):
        from fastapi.responses import FileResponse

        @app.get("/app/{full_path:path}", include_in_schema=False)
        async def frontend_spa_fallback(full_path: str):
            file_path = os.path.join(frontend_dist, full_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(os.path.join(frontend_dist, "index.html"))

    # Store config on app state for access in route handlers
    app.state.config = config

    return app


def create_app_for_testing(
    database_uri: str = "sqlite:///:memory:",
    **kwargs,
) -> FastAPI:
    """Create an application instance for testing with an isolated database.

    Args:
        database_uri: Database URI (defaults to in-memory SQLite).
        **kwargs: Passed to AppConfig.

    Returns:
        FastAPI application instance with test configuration.
    """
    test_db = DatabaseManager(database_uri=database_uri)
    test_db.create_all_tables()
    config = AppConfig(db=test_db, **kwargs)
    return create_app(config)


# Backward-compatible singleton
_app_singleton: Optional[FastAPI] = None


def get_app() -> FastAPI:
    """Get or create the application singleton."""
    global _app_singleton
    if _app_singleton is None:
        _app_singleton = create_app()
    return _app_singleton


def run_api(host, port, **kwargs):
    if kwargs.get("ssl_keyfile") and kwargs.get("ssl_certfile"):
        uvicorn.run(
            get_app(),
            host=host,
            port=port,
            ssl_keyfile=kwargs.get("ssl_keyfile"),
            ssl_certfile=kwargs.get("ssl_certfile"),
        )
    else:
        uvicorn.run(get_app(), host=host, port=port)


def __getattr__(name):
    if name == "app":
        return get_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="langchain-ChatGLM",
        description="About langchain-ChatGLM, local knowledge based ChatGLM with langchain"
        " ｜ 基于本地知识库的 ChatGLM 问答",
    )
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7861)
    parser.add_argument("--ssl_keyfile", type=str)
    parser.add_argument("--ssl_certfile", type=str)
    args = parser.parse_args()

    run_api(
        host=args.host,
        port=args.port,
        ssl_keyfile=args.ssl_keyfile,
        ssl_certfile=args.ssl_certfile,
    )
