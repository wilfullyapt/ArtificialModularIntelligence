from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QWidget

from ..ipc.constants import EventType, ProcessType
from ..ipc.manager import IPCEvent, IPCManager

from .base import BaseIPC, on_event

class IPCQWidget(BaseIPC, QWidget):

    def __init__(self, ipc_manager: IPCManager, process_type: ProcessType):
        QWidget.__init__(self, None)
        BaseIPC.__init__(self, ipc_manager=ipc_manager, process_type=process_type)

        if self.process_manager.stop_flag is not None:
            interval = 100
            self.ipc_timer = QTimer(self)
            self.ipc_timer.timeout.connect(self.ipc_loop)
            self.ipc_timer.start(interval)
            self.ipcgui_info_log("StopFlag timer is running")

    def resizeEvent(self, event):
        self.logs.debug(f"IPCQWidget resize Event: {event}")
        self.a= event
        super().resizeEvent(event)

    def ipcgui_info_log(self, log_message):
        self.logs.info(log_message)
        self.ipc_logs.info(log_message)

    def ipc_loop(self):
        self.check_and_handle_incoming_ipc_event()

        if self.process_manager.stop_flag.is_set():
            self.route_event(
                    IPCEvent(
                        EventType.GLOBAL_STOP,
                        ProcessType.GUI,
                        ProcessType.AI,
                    )
            )
            self.stop()

    @on_event(EventType.GLOBAL_STOP)
    def stop(self):
        """
        Actually perform the shutdown after a brief delay.
        This allows any pending events to be processed.
        """
        self.ipcgui_info_log("Stop Event triggered. Graceful stutdown started.")

        self.ipc_timer.stop()

        if not self.parent():                   # If this has no parents, close the entire application
            if QApplication.instance():         # Check if we're in the main thread
                self.ipc_logs.info("IPCQWidget.stop() :: QApplication found. Closing.")
                self.close()
                QApplication.instance().quit()  # Use quit() to close the application gracefully
            else:
                self.ipc_logs.info("IPCQWidget.stop() :: QApplication not found. Closing.")
                self.close()                    # Fallback to close() if something else is going on
        else:
            self.ipc_logs.info("IPCQWidget.stop() :: Parent not found. Closing.")
            self.close()                        # Just close this widget if it's not the main window

