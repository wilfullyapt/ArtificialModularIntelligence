"""IPC service implementation for Backend communication."""

import asyncio
from typing import Optional, Any
from ami.ipc import IPCServer, ProcessType, EventType, StateType
from ami.ipc.manager import IPCManager
from .markdown_api import MarkdownAPI

class BackendIPCService:
    """
    IPC service implementation for Backend communication.
    Handles markdown operations and other backend services.
    """
    def __init__(
        self,
        manager: IPCManager,
        markdown_api: MarkdownAPI
    ):
        """
        Initialize the Backend service.

        Args:
            manager (IPCManager): IPC manager instance
            markdown_api (MarkdownAPI): Markdown API instance
        """
        self.markdown_api = markdown_api
        self.server = IPCServer(ProcessType.BACKEND, manager)

        # Register command handlers
        self.server.register_command("process_markdown", self._handle_process_markdown)
        self.server.register_command("save_markdown", self._handle_save_markdown)
        self.server.register_command("load_markdown", self._handle_load_markdown)

        # Register event handlers
        self.server.on_event(EventType.ERROR, self._handle_error)

    async def _handle_process_markdown(self, source: ProcessType, args: tuple[str, asyncio.Future]) -> str:
        """Handle markdown processing command."""
        markdown_text, result_future = args
        try:
            processed_text = await self.markdown_api.process_markdown(markdown_text)
            result_future.set_result(processed_text)
            return "success"
        except Exception as e:
            result_future.set_exception(e)
            return str(e)

    async def _handle_save_markdown(self, source: ProcessType, args: tuple[str, str, asyncio.Future]) -> str:
        """Handle markdown save command."""
        filename, content, result_future = args
        try:
            success = await self.markdown_api.save_markdown(filename, content)
            result_future.set_result(success)
            return "success"
        except Exception as e:
            result_future.set_exception(e)
            return str(e)

    async def _handle_load_markdown(self, source: ProcessType, args: tuple[str, asyncio.Future]) -> str:
        """Handle markdown load command."""
        filename, result_future = args
        try:
            content = await self.markdown_api.load_markdown(filename)
            result_future.set_result(content)
            return "success"
        except Exception as e:
            result_future.set_exception(e)
            return str(e)

    async def _handle_error(self, event: Any):
        """Handle error events."""
        print(f"Backend error: {event.data}")

    async def start(self) -> None:
        """Start the IPC server."""
        self.server.start()
        print("Backend IPC server ready")

    async def stop(self) -> None:
        """Stop the IPC server."""
        self.server.stop()