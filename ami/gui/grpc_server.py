"""
GUI gRPC server implementation for handling UI events
"""

import time
import grpc
from concurrent import futures
from typing import Optional, Dict, Any
from queue import Queue

from ami.core.config import Config
from ami.core.logging import Logger
from ami.protos.generated import gui_service_pb2_grpc
from ami.protos.generated import gui_service_pb2

class GUIServicer(gui_service_pb2_grpc.GUIServiceServicer):
    """Servicer for GUI events"""
    
    def __init__(self, event_queue: Queue, logger: Logger):
        self.event_queue = event_queue
        self.logger = logger

    async def StreamEvents(self, request_iterator, context):
        """Handle incoming event stream from AI"""
        try:
            async for event in request_iterator:
                # Put event in queue for GUI to process
                self.event_queue.put((event.type, event.data))
                
                # Send acknowledgment
                yield gui_service_pb2.GuiEventResponse(
                    success=True,
                    message="Event received"
                )
        except Exception as e:
            self.logger.error(f"Error in StreamEvents: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            yield gui_service_pb2.GuiEventResponse(
                success=False,
                message=f"Error: {str(e)}"
            )

class GUIServer:
    """gRPC server for GUI events"""

    def __init__(self, event_queue: Queue, config: Config, logger: Logger):
        self.event_queue = event_queue
        self.config = config
        self.logger = logger
        self._server = None

    def start(self):
        """Start the gRPC server"""
        if self._server:
            self.logger.warning("Server already running")
            return

        self._server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 50 * 1024 * 1024),
                ('grpc.max_receive_message_length', 50 * 1024 * 1024),
                ('grpc.keepalive_time_ms', 20000),
                ('grpc.keepalive_timeout_ms', 10000),
                ('grpc.keepalive_permit_without_calls', True),
                ('grpc.http2.max_pings_without_data', 0),
                ('grpc.http2.min_time_between_pings_ms', 10000),
            ]
        )

        # Add the servicer to the server
        servicer = GUIServicer(self.event_queue, self.logger)
        gui_service_pb2_grpc.add_GUIServiceServicer_to_server(servicer, self._server)

        # Get host and port from config
        host = self.config.get('gui_server_host', '[::]')
        port = self.config.get('gui_server_port', 50052)

        # Start the server
        address = f"{host}:{port}"
        self._server.add_insecure_port(address)
        await self._server.start()

        self.logger.info(f"GUI gRPC server started on {address}")

    async def stop(self):
        """Stop the gRPC server gracefully"""
        if not self._server:
            return

        # Give grace period for existing calls to complete
        await self._server.stop(grace=5)
        self._server = None
        self.logger.info("GUI gRPC server stopped")