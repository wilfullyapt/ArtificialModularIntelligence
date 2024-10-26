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

from pydantic import ValidationError

from ami.base import Base
from ami.config import Config
from ami.headspace.blueprint import Payload
from ami.flask.manager import FlaskManager, create_flask_app

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
        mechanism, temporal communications, ears, GUI, Flask manager, and brain components.
        """
        super().__init__()

        self.async_thread = None
        self.ai_pipe, self.flask_pipe = Pipe()
        self.stop_event = MultiprocessEvent()

        enabled_headspaces = Config().enabled_headspaces
        self.submodules = ('headspace', 'blueprint', 'gui', 'prompts')
        self._core_modules: List[ModuleType] = self._load_core_modules(enabled_headspaces)
#         self._core_modules = ( "markdown",)

        from . import Attention, Brain
        from ami.ears import Ears
        from ami.gui import GUI

        self.attn = Attention(ignore_coroname_logging=["process_whisperer"])

        self.temp_comms = TemporalCommunications()
        self.ears = Ears(temp_comms=self.temp_comms)

        self.gui = GUI(temp_comms=self.temp_comms)
        self.flask_manager = FlaskManager(self.stop_event)
        self.brain = Brain(temp_comms=self.temp_comms, headspaces=self.get_modules_part("headspace"))

        self.establish_temporal_communications()

    @property
    def server_url(self):
        """ Return the URL of the flask app """
        return self.flask_manager.url

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

        app = create_flask_app(self.get_modules_part("blueprint"), self.flask_pipe)
        self.flask_manager.start(app)

        self.ears.start_listening()
        self.attn.start()
        self.attn.schedule(self.process_whisperer())

#       self.gui.run(builtins=self.get_builtin_guis(), modules=self.get_modules_part("gui"))
        self.gui.run(self.get_modules_part("gui"))  # The GUI must run in the main thread

        self.stop()                                 # If the GUI closes, everything else should

    def stop(self, event=None, frame=None):
        """ Stop all composed object """
        self.logs.debug("AI.stop() called!!!")
        self.flask_manager.stop()
        self.ears.stop()
        self.gui.stop()
        self.attn.stop()

    def establish_temporal_communications(self):
        """ Core temporal communication pipelines """
        self.temp_comms.subscribe("ears.hotword_detected", self.start_chat)
        self.temp_comms.subscribe("ears.recorder_callback", self.human_to_ai)
        self.temp_comms.subscribe("ears.timeout", self.gui.popup.close)
        self.temp_comms.subscribe("gui.popup.loading_message", self.gui.popup.set_loading_message)
        self.temp_comms.subscribe("gui.interaction_finished", self.ears.start_listening)
        self.temp_comms.subscribe("attn.schedule", self.attn.schedule)

    def start_chat(self):
        """ Initiate the chat in the GUI """
        async def _start_chat():

            self.gui.create_popup()

        self.attn.schedule(_start_chat())

    def human_to_ai(self, message):
        """ Handle the what the GUI should show, query the brain with the message """
        if message is False:
            self.logs.warn("AI recieved no input! Cancelling interaction!")
            return

        async def _human_to_ai(message):
            """ async function that does all the work """
            self.gui.popup.set_human_message(message)
            dialog = self.brain.query(message, load_msg_callback=self.gui.popup.set_loading_message)
#           self.q = dialog
            self.gui.popup.set_ai_response(dialog)

        self.attn.schedule(_human_to_ai(message))

    def handle_payload(self, payload: Payload):
        """ Accept a Payload object, do it's bidding """
        if payload.module.lower() in [ cm.__name__.split('.')[-1] for cm in self.core_modules ]:
            if payload.reload:
                self.gui.reload_child(payload.module)

        else:
            self.logs.error(f"Module `{payload.module}` invalid!")

    async def process_whisperer(self):
        """ Scheduled in the Attention recursively. Watches the IPC and handles events """
        if self.stop_event.is_set():
            self.gui.stop()

        if self.ai_pipe.poll():
            try:
                data = self.ai_pipe.recv()
                payload = pickle.loads(data)

                if isinstance(payload, Payload):
                    self.handle_payload(payload)
                else:
                    raise ValueError("Received data is not a valid Payload object")

            except pickle.UnpicklingError as e:
                self.logs.error(f"Failed to unpickle payload: {e}")
            except ValidationError as e:
                self.logs.error(f"Invalid payload format: {e}")
            except EOFError as e:
                self.logs.error(f"EOF error while reading from pipe: {e}")
            except Exception as e:
                self.logs.error(f"Unexpected error processing payload: {e}")

        else:
            await asyncio.sleep(1)

        self.attn.schedule(self.process_whisperer())
