"""gRPC client for communicating with AI service"""
import grpc
from ami.protos.generated import ai_service_pb2, ai_service_pb2_grpc

class AIClient:
    """Client for communicating with AI gRPC service"""
    
    def __init__(self):
        """Initialize the AI client"""
        self.channel = grpc.aio.insecure_channel('localhost:53848')  # AI gRPC server port
        self.stub = ai_service_pb2_grpc.AIServiceStub(self.channel)

    async def query(self, message: str) -> str:
        """Send a query to the AI service"""
        try:
            request = ai_service_pb2.QueryRequest(message=message)
            response = await self.stub.Query(request)
            return response.response
        except Exception as e:
            raise Exception(f"Failed to query AI service: {e}")

    async def process_audio(self, audio_data: bytes) -> str:
        """Send audio data for processing"""
        try:
            request = ai_service_pb2.AudioData(audio_data=audio_data)
            response = await self.stub.ProcessAudio(request)
            return response.text
        except Exception as e:
            raise Exception(f"Failed to process audio: {e}")

    async def generate_audio(self, text: str) -> bytes:
        """Request audio generation from text"""
        try:
            request = ai_service_pb2.TextRequest(text=text)
            response = await self.stub.GenerateAudio(request)
            return response.audio_data
        except Exception as e:
            raise Exception(f"Failed to generate audio: {e}")

    async def close(self):
        """Close the gRPC channel"""
        await self.channel.close()