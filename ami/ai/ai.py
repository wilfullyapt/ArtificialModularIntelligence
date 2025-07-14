"""Main AI orchestrator module"""
import sys
import asyncio
from pathlib import Path
from types import ModuleType
import importlib.util as importer
from functools import cached_property
from typing import Any, List, Literal, Optional, Type
from queue import Empty

from ami.core import Config
from ami.ipc import ProcessIPC, IPCManager, ProcessType, EventType, StateType, IPCEvent, on_event
from ami.headspace.blueprint import Payload

from .listener import Listener

class AI(ProcessIPC):
    """
    The AI class represents the core Artificial Modular Intelligence system.
    """

    def __init__(self, process_manager: IPCManager):
        """ Initialize the AI instance. """
        ProcessIPC.__init__(self, process_manager, ProcessType.AI)

        enabled_headspaces = Config().enabled_headspaces
        self.submodules = ('headspace', 'blueprint', 'gui', 'prompts')
        self._core_modules = enabled_headspaces

    @cached_property
    def listener(self):
        def queue_event(event_type: EventType, data: Any):
            event = IPCEvent(
                type=event_type,
                source=ProcessType.AI,
                target=ProcessType.GUI,
                data=data
            )
            self.get_queue(ProcessType.AI).put(event)
        return Listener(queue_event)

    def setup(self):
        """ Subclassed from BaseProcess for the process setup """
        try:
#           self.process_manager.set_state(StateType.IDLE)
            self.logs.info("Setup function called")
            self.listener.start_listening()
            self.running(True)
#           self.process_manager.set_state(StateType.WAITING)

        except Exception as e:
            self.logs.error(f"Error in setup: {e}")
#           self.process_manager.set_state(StateType.ERROR)
            raise

    def loop(self):
        """ Subclassed from BaseProcess for the process loop """
        pass


    @on_event(EventType.HOTWORD_DETECTED)
    def _handle_hotword(self, event: IPCEvent):
        """Handle hotword detection"""
        self.route_event(event.forward(ProcessType.GUI))
        self.logs.debug("HOTWORD_DETECTED event triggered!")

    @on_event(EventType.TRANSCRIPTION_READY)
    def _handle_transcription(self, event: IPCEvent):
        """Handle transcription completion"""
        self.route_event(event.forward(ProcessType.GUI))
        self.logs.info(f"AI.IPCEvent(TRANSCRIPTION_READY): {event.data}")

        response = self.query(event.data)
        self.route_event(IPCEvent(EventType.RESPONSE_READY, ProcessType.AI, ProcessType.GUI, response))
        self.logs.info(f"AI.IPCEvent(RESPONSE_READY): {response}")
#       self.process_manager.set_state(StateType.WAITING)

    @on_event(EventType.INTERACTION_COMPLETED)
    def restart_hotword_detection(self, event: IPCEvent):
        self.listener.start_listening()

    @on_event(EventType.ERROR)
    def _handle_error(self, event: IPCEvent):
        """Handle error events"""
        self.logs.error(f"Error event received: {event.data}")
        self.process_manager.set_state(StateType.ERROR)

    def query(self, message: str) -> str:
        """Query the AI with a message and return the response"""
        try:
            # First try to process locally with brain
#           response = self.brain.query(message)        # DEPRICATE
            response = message[::-1]
            return response
        except Exception as e:
            self.logs.error(f"Local brain query failed: {e}")

    @on_event(EventType.GLOBAL_STOP)
    def cleanup(self, event: IPCEvent):
        """Clean up AI resources"""
        self.logs.debug("AI cleanup called. Listening thread to terminate.")
        self.logs.debug(f"Event: {event}")
        try:
            if hasattr(self, 'listener'):
                self.listener.stop_listening()
                self.logs.info("Cleanup: AI resources cleaned up")
            else:
                self.logs.info("Cleanup: No AI resources needed to be cleaned")

        except Exception as e:
            self.logs.error(f"Error during AI cleanup: {e}")

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

    def handle_payload(self, payload: Payload):
        """ Accept a Payload object, do it's bidding """
        if payload.module.lower() in [ cm.__name__.split('.')[-1] for cm in self.core_modules ]:
            if payload.reload:
                self.gui.reload_child(payload.module)

        else:
            self.logs.error(f"Module `{payload.module}` invalid!")
