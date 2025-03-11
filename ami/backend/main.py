import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging

from ami.backend.markdown_api import app as markdown_app
from ami.backend.log_api import app as log_app
from ami.backend.settings_api import app as settings_app

logger = logging.getLogger(__name__)

def create_app(
    enable_markdown: bool = True,
    enable_logs: bool = True,
    enable_settings: bool = True
) -> FastAPI:
    """
    Create the FastAPI application with specified components enabled.
    Useful for testing specific components or running partial services.
    """
    app = FastAPI(title="AMI Backend API")

    # Configure CORS for React frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:52563"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount enabled components
    if enable_markdown:
        app.mount("/markdown", markdown_app)
        logger.info("Markdown API enabled")

    if enable_logs:
        app.mount("/logs", log_app)
        logger.info("Log API enabled")

    if enable_settings:
        app.mount("/settings", settings_app)
        logger.info("Settings API enabled")

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "components": {
                "markdown": enable_markdown,
                "logs": enable_logs,
                "settings": enable_settings
            }
        }

    return app

# Default application instance with all components enabled
app = create_app()

def run_server(
    host: str = "0.0.0.0",
    port: int = 58744,
    reload: bool = False,
    enable_markdown: bool = True,
    enable_logs: bool = True,
    enable_settings: bool = True,
    log_level: str = "info"
):
    """
    Run the FastAPI server with specified configuration.
    This can be used for both subprocess and main process execution.
    """
    app_instance = create_app(
        enable_markdown=enable_markdown,
        enable_logs=enable_logs,
        enable_settings=enable_settings
    )

    config = uvicorn.Config(
        app=app_instance,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AMI Backend Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=58744, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--no-markdown", action="store_true", help="Disable markdown API")
    parser.add_argument("--no-logs", action="store_true", help="Disable logs API")
    parser.add_argument("--no-settings", action="store_true", help="Disable settings API")
    parser.add_argument("--log-level", default="info", help="Logging level")

    args = parser.parse_args()

    run_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
        enable_markdown=not args.no_markdown,
        enable_logs=not args.no_logs,
        enable_settings=not args.no_settings,
        log_level=args.log_level
    )