"""
Base gRPC server implementation with support for both unary and streaming responses
"""

import grpc
from concurrent import futures
import threading
from typing import Optional, Callable, Dict, Any
from ami.core.config import Config
from ami.core.logging import Logger
from ami.protos.generated import ai_service_pb2_grpc
from ami.protos.generated import ai_service_pb2

class BaseServicer(ai_service_pb2_grpc.AIServiceServicer):
    """Base servicer class that can be extended by specific implementations"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        
    def ProcessText(self, request, context):
        """
        Override this method in your implementation
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')
        
    def ProcessAudio(self, request, context):
        """
        Override this method in your implementation
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

class GRPCServer:
    """
    Base gRPC server class with graceful shutdown and health checking
    """
    
    def __init__(self, servicer: BaseServicer, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.servicer = servicer
        self._server = None
        self._should_stop = threading.Event()
        
        # Register config watcher for port/host changes
        self.config.add_observer(self._handle_config_change)
        
    def _handle_config_change(self, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """Handle configuration changes"""
        if (old_config.get('port') != new_config.get('port') or 
            old_config.get('host') != new_config.get('host')):
            self.logger.info("Server configuration changed, restarting server...")
            self.stop()
            self.start()
    
    def start(self):
        """Start the gRPC server"""
        if self._server:
            self.logger.warning("Server already running")
            return
            
        self._should_stop.clear()
        self._server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
                ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50MB
                ('grpc.keepalive_time_ms', 20000),  # 20 seconds
                ('grpc.keepalive_timeout_ms', 10000),  # 10 seconds
                ('grpc.keepalive_permit_without_calls', True),
                ('grpc.http2.max_pings_without_data', 0),
                ('grpc.http2.min_time_between_pings_ms', 10000),  # 10 seconds
            ]
        )
        
        # Add the servicer to the server
        ai_service_pb2_grpc.add_AIServiceServicer_to_server(self.servicer, self._server)
        
        # Add health checking service
        health_servicer = grpc.health.v1.health_pb2_grpc.add_HealthServicer_to_server(
            grpc.health.v1.HealthServicer(), self._server)
            
        # Get host and port from config
        host = self.config.server_host or '[::]'
        port = self.config.server_port or 50051
        
        # Start the server
        address = f"{host}:{port}"
        self._server.add_insecure_port(address)
        self._server.start()
        
        self.logger.info(f"gRPC server started on {address}")
        
    def stop(self):
        """Stop the gRPC server gracefully"""
        if not self._server:
            return
            
        self._should_stop.set()
        
        # Give grace period for existing calls to complete
        self._server.stop(grace=5)
        self._server = None
        self.logger.info("gRPC server stopped")
        
    def wait_for_termination(self):
        """Wait for the server to terminate"""
        if not self._server:
            return
            
        try:
            while not self._should_stop.is_set():
                self._should_stop.wait(timeout=1)
        except KeyboardInterrupt:
            self.stop()
            
    def __enter__(self):
        """Context manager support"""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure server is stopped when exiting context"""
        self.stop()