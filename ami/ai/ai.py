"""Main AI orchestrator module"""
import asyncio
from functools import cached_property
from typing import Any

from ami.core.conversation import Conversation
from ami.ipc import ProcessIPC, IPCManager, ProcessType, EventType, StateType, IPCEvent, on_event
from ami.headspace.blueprint import Payload
from ami.headspace.plugin_base import PluginType, PluginSource

from .brain import Brain
from .listener import Listener

class AI(ProcessIPC):
    """
    The AI class represents the core Artificial Modular Intelligence system.
    
    This class manages:
    - Plugin loading and lifecycle (through PluginRegistry)
    - Event handling and IPC
    - Audio input through Listener
    - Query processing through Brain
    """

    def __init__(self, process_manager: IPCManager):
        """Initialize the AI instance."""
        ProcessIPC.__init__(self, process_manager, ProcessType.AI)
#       config = Config()
        self.convo = Conversation()
        
    @cached_property
    def brain(self) -> Brain:
        """Get or create the audio listener."""
        return Brain(self.process_manager)

    @cached_property
    def listener(self):
        """Get or create the audio listener."""
        def queue_event(event_type: EventType, data: Any):
            event = IPCEvent(
                type=event_type,
                source=ProcessType.AI,
                target=ProcessType.GUI,
                data=data
            )
            self.get_queue(ProcessType.AI).put(event)
        return Listener(queue_event)

    async def setup(self):
        """Set up the AI system."""
        try:
            self.logs.info("Setting up AI system")
            
            # Start the listener
            self.listener.start_listening()
            
            # Load enabled plugins
            config = Config()

            for plugin_name in config.enabled_headspaces:
                await self.plugin_registry.load_plugin(plugin_name)
            
            self.running(True)

        except Exception as e:
            self.logs.error(f"Error in setup: {e}")
            self.process_manager.set_state(StateType.ERROR)
            raise

    async def loop(self):
        """Main processing loop."""
        # This could be used for periodic tasks like plugin health checks
        await asyncio.sleep(1)

    @on_event(EventType.PLUGIN_CHANGED)
    def _on_plugin_changed(self, ipc_event: IPCEvent):
        # TODO: Nothing? Does a directory change (repo clone) mean anything to this class?
        pass

    @on_event(EventType.METADATA_CHANGED)
    def _on_metadata_changed(self, ipc_event: IPCEvent):
        # TODO: Check to see if this enabled a plugin
#       self.brain.resync()         # This should get a diff between the old and new and know what to do
        pass

    @on_event(EventType.CONFIG_CHANGED)
    def _on_config_changed(self, ipc_event: IPCEvent):
        # TODO: ? Thinking about a string:class_method style reloading per config option
        pass

    @on_event(EventType.HOTWORD_DETECTED)
    def _on_hotword_detected(self, event: IPCEvent):
        """Handle hotword detection."""
        self.route_event(event.forward(ProcessType.GUI))
        self.logs.debug("Hotword detected")
        if not self.convo.is_blank():
            self.logs.error("AI.convo is found non-blank during a Hotword Detection Event!")
            self.convo = Conversation()

    @on_event(EventType.TRANSCRIPTION_READY)
    async def _on_transcription_ready(self, event: IPCEvent):
        """Handle transcription completion."""
        self.route_event(event.forward(ProcessType.GUI))
        self.logs.info(f"Transcription ready: {event.data}")

        self.convo.add_message(event.data, role="human")                # Add the Human message
        self.process_manager.set_conversation(self.convo.to_dict())     # Updated ipc shared convo

        response = self.brain.query(self.convo)                         # Query the brain against the convo
        
        self.convo.add_message(response, role="ai")                     # Add the AI response to the convo
        self.process_manager.set_conversation(self.convo.to_dict())     # Update the ipc shared convo

        # Route response to GUI
        self.route_event(IPCEvent(
            EventType.RESPONSE_READY, 
            ProcessType.AI, 
            ProcessType.GUI, 
            response
        ))
        self.logs.info(f"Response ready: {response}")

    @on_event(EventType.INTERACTION_COMPLETED)
    def restart_hotword_detection(self, event: IPCEvent):
        """Restart hotword detection after interaction."""
        self.convo = Conversation()
        self.listener.start_listening()

    @on_event(EventType.ERROR)
    def _handle_error(self, event: IPCEvent):
        """Handle error events."""
        self.logs.error(f"Error event received: {event.data}")
        self.process_manager.set_state(StateType.ERROR)

    @on_event(EventType.GLOBAL_STOP)
    async def cleanup(self, event: IPCEvent):
        """Clean up AI resources."""
        self.logs.debug("Cleaning up AI resources")
        try:
            if hasattr(self, 'listener'):
                self.listener.stop_listening()
            
            self.logs.info("AI resources cleaned up")

        except Exception as e:
            self.logs.error(f"Error during cleanup: {e}")
