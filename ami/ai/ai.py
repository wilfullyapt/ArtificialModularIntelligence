""" The main attraction """
import sys
import signal
import pickle
import asyncio
import importlib.util as importer
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, List, Literal, Optional, Type
from multiprocessing import Pipe, Event as MultiprocessEvent

import grpc
from pydantic import ValidationError

from ami.base import Base
from ami.config import Config
from ami.headspace.blueprint import Payload
from ami.protos.generated import ai_service_pb2, ai_service_pb2_grpc

class TemporalCommunications:
    """
    A class for implementing the Observer pattern, allowing objects to subscribe
    to and publish events.
    """
    def __init__(self):
        """
        Initialize the TemporalCommunications instance with an empty dictionary
        to store subscribers.
        """
        self.subscribers = {}

    def subscribe(self, event, callback: Callable):
        """
        Subscribe a callable (function or method) to an event.

        Args:
            event (str): The name of the event to subscribe to.
            callback (Callable): The callable to be invoked when the event is published.
        """
        if event not in self.subscribers:
            self.subscribers[event] = []
        self.subscribers[event].append(callback)

    def publish(self, event, data=None):
        """
        Publish an event, invoking all subscribed callables.

        Args:
            event (str): The name of the event to publish.
            data (optional): Data to be passed to the subscribed callables.
        """
        if event in self.subscribers:
            for callback in self.subscribers[event]:
                if data is None:
                    callback()
                else:
                    callback(data)

class AI(Base):
    """
    The AI class represents the core Artificial Modular Intelligence system.

    This class integrates various components such as attention management,
    brain processing, audio input (ears), graphical user interface, and
    inter-process communication. It manages the initialization, running,
    and stopping of these components, as well as handling payloads for
    module management and GUI updates.

    Attributes:
        async_thread (Thread): Thread for asynchronous operations by the Attention.
        ai_pipe (Connection): Pipe inter-process communication from the Flask server.
        flask_pipe (Connection): Pipe inter-process communication for the Flask server.
        stop_event: multiprocesses.Event to signal stopping of the AI system.
        _core_modules (MultiprocessEvent): List of core module names or loaded module objects.
        attn (Attention): Attention management component, basically an async event loop.
        temp_comms (TemporalCommunications): Observer pattern Event Bus.
        ears (Ears): Audio input component.
        gui (GUI): Tkinter Graphical user interface component.
        flask_manager (FlaskManager): Manager for the Flask app and Gunicorn.
        brain (Brain): LLM powerhouse and Headspace manager.

    Inherits from:
        Base: Provides basic functionality and logging capabilities.
    """

    def __init__(self):
        """
        Initialize the AI instance.

        This method sets up the necessary components and configurations for the AI system.
        It loads the core modules based on the enabled headspaces, initializes the attention
        mechanism, temporal communications, and brain components.
        """
        super().__init__()

        self.async_thread = None
        self.stop_event = MultiprocessEvent()

        enabled_headspaces = Config().enabled_headspaces
        self.submodules = ('headspace', 'blueprint', 'gui', 'prompts')
        self._core_modules: List[ModuleType] = self._load_core_modules(enabled_headspaces)

        from . import Attention, Brain
        from ami.ears import Ears

        # Initialize gRPC client for backend communication
        self.channel = grpc.aio.insecure_channel('localhost:59195')  # Backend gRPC port
        self.backend_stub = ai_service_pb2_grpc.AIServiceStub(self.channel)

        self.attn = Attention(ignore_coroname_logging=["process_whisperer"])
        self.temp_comms = TemporalCommunications()
        self.ears = Ears(temp_comms=self.temp_comms)
        self.brain = Brain(temp_comms=self.temp_comms, headspaces=self.get_modules_part("headspace"))

        self.establish_temporal_communications()

    async def query(self, message: str) -> str:
        """Query the AI with a message and return the response"""
        try:
            # First try to process locally with brain
            response = self.brain.query(message)
            return response
        except Exception as e:
            self.logs.error(f"Local brain query failed: {e}")
            try:
                # Fallback to backend service
                request = ai_service_pb2.QueryRequest(message=message)
                response = await self.backend_stub.Query(request)
                return response.response
            except Exception as e:
                self.logs.error(f"Backend query failed: {e}")
                return "I apologize, but I'm having trouble processing your request."

    async def process_audio(self, audio_data: bytes) -> str:
        """Process audio data and return transcribed text"""
        try:
            request = ai_service_pb2.AudioData(audio_data=audio_data)
            response = await self.backend_stub.ProcessAudio(request)
            return response.text
        except Exception as e:
            self.logs.error(f"Audio processing failed: {e}")
            return ""

    async def generate_audio(self, text: str) -> bytes:
        """Generate audio from text"""
        try:
            request = ai_service_pb2.TextRequest(text=text)
            response = await self.backend_stub.GenerateAudio(request)
            return response.audio_data
        except Exception as e:
            self.logs.error(f"Audio generation failed: {e}")
            return bytes()

    def import_headspace_module(self, module_path: Path, mode: Literal["core", "import"]="import") -> ModuleType:
        """
        Import a headspace module from the specified path.

        Args:
            module_path (Path): The path to the headspace module directory.
            mode (Literal["core", "import"], optional): The mode for importing the module.
                                                        Defaults to "import".

        Returns:
            ModuleType: The imported module object.
        """
        module_name = f"ami.headspace.__{mode}_headspace__.{module_path.name}"

        def load_module(name: str, path: Path) -> Optional[ModuleType]:
            if not path.exists():
                return None
            try:
                spec = importer.spec_from_file_location(name, str(path))
                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not load module {name} from {path}")
                module = importer.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
                return module
            except ImportError as e:
                # Print the traceback and the name of the module that failed to import
                import traceback
                self.logs.error(f"Failed to import {name}: {e}")
                self.logs.error(traceback.format_exc())
                return None

        main_module_path = module_path / "__init__.py"
        main_module = load_module(module_name, main_module_path)
        if main_module is None:
            self.logs.error(f"Failed to load main module from {main_module_path}")
            raise ImportError(f"Failed to load main module from {main_module_path}")

        main_module.__path__ = [str(module_path)]

        for submodule_name in self.submodules:
            full_name = f"{module_name}.{submodule_name}"
            submodule_path = module_path / f"{submodule_name}.py"
            submodule = load_module(full_name, submodule_path)
            if submodule:
                setattr(main_module, submodule_name, submodule)

        return main_module

    def _load_core_modules(self, enabled_headspaces) -> List[ModuleType]:
        core_modules_path = Path(__file__).parent.parent / "headspace" / "core"
        return_modules = []
        for module_name in enabled_headspaces:
            try:
                module = self.import_headspace_module(core_modules_path / module_name, mode="core")
                return_modules.append(module)
            except ImportError as e:
                self.logs.error(f"Failed to load module {module_name}: {e}")
        return return_modules

    @property
    def core_modules(self) -> List[ModuleType]:
        """ return self._core_modules """
        return self._core_modules

    def get_modules_part(self, part: Literal['gui', 'headspace', 'blueprint']) -> List[Type[Any]]:
        """ Get a specific element (e.g. part Literal) from all modules """
        def get_name(module: ModuleType) -> str:
            name = module.__name__.split('.')[-2].capitalize()
            if hasattr(module, name):
                return name
            return ""
        modules = [ getattr(module, part) for module in self.core_modules if hasattr(module, part) ]
        return [ getattr(module, get_name(module)) for module in modules if get_name(module) ]

    def run(self):
        """ Run the AI """
        signal.signal(signal.SIGINT, self.stop)

        self.ears.start_listening()
        self.attn.start()
        self.attn.schedule(self.process_whisperer())

        # Keep running until stop event is set
        try:
            while not self.stop_event.is_set():
                signal.pause()
        except (KeyboardInterrupt, SystemExit):
            self.stop()

    def stop(self, event=None, frame=None):
        """ Stop all composed object """
        self.logs.debug("AI.stop() called!!!")
        self.ears.stop()
        self.attn.stop()
        self.stop_event.set()
        if hasattr(self, 'channel'):
            asyncio.run(self.channel.close())

    def establish_temporal_communications(self):
        """ Core temporal communication pipelines """
        self.temp_comms.subscribe("ears.recorder_callback", self.process_input)
        self.temp_comms.subscribe("attn.schedule", self.attn.schedule)

    async def process_input(self, message):
        """ Process input from ears or other sources """
        if message is False:
            self.logs.warn("AI received no input! Cancelling interaction!")
            return

        try:
            # Try to process audio if message is bytes
            if isinstance(message, bytes):
                text = await self.process_audio(message)
                if not text:
                    return
                message = text

            # Get AI response
            response = await self.query(message)

            # Generate audio response if needed
            if self.ears.is_listening:
                audio_data = await self.generate_audio(response)
                if audio_data:
                    self.ears.play_audio(audio_data)

            return response

        except Exception as e:
            self.logs.error(f"Error in process_input: {e}")
            return "I apologize, but I encountered an error processing your request."

    def handle_payload(self, payload: Payload):
        """ Accept a Payload object, do it's bidding """
        if payload.module.lower() in [ cm.__name__.split('.')[-1] for cm in self.core_modules ]:
            if payload.reload:
                self.gui.reload_child(payload.module)

        else:
            self.logs.error(f"Module `{payload.module}` invalid!")

    async def process_whisperer(self):
        """ Scheduled in the Attention recursively. Watches for events and handles them """
        if self.stop_event.is_set():
            return

        # Process any pending events or tasks here
        await asyncio.sleep(1)

        # Reschedule this coroutine
        self.attn.schedule(self.process_whisperer())
