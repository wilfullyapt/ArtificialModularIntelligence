"""
Base gRPC client implementation with support for both unary and streaming calls
"""

import grpc
from typing import Optional, Generator, Dict, Any
import backoff
from ami.core.config import Config
from ami.core.logging import Logger
from ami.protos.generated import ai_service_pb2_grpc
from ami.protos.generated import ai_service_pb2

class GRPCClient:
    """
    Base gRPC client with automatic reconnection and configuration updates
    """
    
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self._channel = None
        self._stub = None
        
        # Register config watcher
        self.config.add_observer(self._handle_config_change)
        
    def _handle_config_change(self, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """Handle configuration changes"""
        if (old_config.get('port') != new_config.get('port') or 
            old_config.get('host') != new_config.get('host')):
            self.logger.info("Client configuration changed, reconnecting...")
            self.disconnect()
            self.connect()
    
    @property
    def channel(self) -> grpc.Channel:
        """Get the current channel, creating it if necessary"""
        if not self._channel:
            self.connect()
        return self._channel
    
    @property
    def stub(self) -> ai_service_pb2_grpc.AIServiceStub:
        """Get the current stub, creating it if necessary"""
        if not self._stub:
            self._stub = ai_service_pb2_grpc.AIServiceStub(self.channel)
        return self._stub
    
    def connect(self):
        """
        Establish connection to the gRPC server with automatic retry
        """
        if self._channel:
            return
            
        host = self.config.server_host or 'localhost'
        port = self.config.server_port or 50051
        address = f"{host}:{port}"
        
        self._channel = grpc.insecure_channel(
            address,
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
        
        # Create new stub
        self._stub = ai_service_pb2_grpc.AIServiceStub(self._channel)
        self.logger.info(f"Connected to gRPC server at {address}")
    
    def disconnect(self):
        """Close the current connection"""
        if self._channel:
            self._channel.close()
            self._channel = None
            self._stub = None
            self.logger.info("Disconnected from gRPC server")
    
    @backoff.on_exception(
        backoff.expo,
        (grpc.RpcError, grpc.FutureTimeoutError),
        max_tries=5
    )
    def process_text(self, text: str, timeout: Optional[float] = None) -> ai_service_pb2.TextResponse:
        """
        Process text request with automatic retry on failure
        """
        request = ai_service_pb2.TextRequest(text=text)
        try:
            response = self.stub.ProcessText(request, timeout=timeout)
            return response
        except grpc.RpcError as e:
            self.logger.error(f"Error processing text: {e}")
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                self.disconnect()  # Force reconnection on next attempt
            raise
    
    @backoff.on_exception(
        backoff.expo,
        (grpc.RpcError, grpc.FutureTimeoutError),
        max_tries=5
    )
    def process_audio(self, audio_data: bytes, format: str, timeout: Optional[float] = None) -> ai_service_pb2.TextResponse:
        """
        Process audio request with automatic retry on failure
        """
        request = ai_service_pb2.AudioRequest(audio_data=audio_data, format=format)
        try:
            response = self.stub.ProcessAudio(request, timeout=timeout)
            return response
        except grpc.RpcError as e:
            self.logger.error(f"Error processing audio: {e}")
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                self.disconnect()  # Force reconnection on next attempt
            raise
    
    def __enter__(self):
        """Context manager support"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure connection is closed when exiting context"""
        self.disconnect()
        
    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()