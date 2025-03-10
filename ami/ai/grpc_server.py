"""gRPC server implementation for AI service"""
import grpc
from ami.protos.generated import ai_service_pb2, ai_service_pb2_grpc

class AIServiceServicer(ai_service_pb2_grpc.AIServiceServicer):
    """Implementation of AIService gRPC service"""
    
    def __init__(self, ai_instance):
        """Initialize with an AI instance"""
        self.ai = ai_instance

    async def Query(self, request, context):
        """Handle AI query requests"""
        try:
            response = await self.ai.query(request.message)
            return ai_service_pb2.QueryResponse(response=response)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.QueryResponse()

    async def ProcessAudio(self, request, context):
        """Handle audio processing requests"""
        try:
            text = await self.ai.process_audio(request.audio_data)
            return ai_service_pb2.AudioResponse(text=text)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.AudioResponse()

    async def GenerateAudio(self, request, context):
        """Handle text-to-speech requests"""
        try:
            audio_data = await self.ai.generate_audio(request.text)
            return ai_service_pb2.AudioData(audio_data=audio_data)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.AudioData()