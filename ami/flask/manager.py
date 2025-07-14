""" Manager for the Flask Server """

import multiprocessing
from typing import List, Type
import socket

from gunicorn.app.base import BaseApplication

from ..core import LogBase, Config, PluginRegistry, PluginVertical
from ..ipc import IPCManager

from .server import assemble_flask_server

def get_network_url(remote_host="www.x.com" ):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        remote_ip = socket.gethostbyname(remote_host)
        s.connect((remote_ip, 80))
        ip_address = s.getsockname()[0]
        s.close()
        port = Config().server_port
        return f"{ip_address}:{port}"
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

class GunicornServer(BaseApplication):
    """
    A custom Gunicorn server application that extends the BaseApplication class.
    This class is responsible for loading and running the Flask application
    with the specified configuration options.
    """
    def __init__(self, application, options=None):
        """
        Initialize the GunicornServer instance.

        Args:
            application (Flask): The Flask application instance to be served.
            options (dict, optional): A dictionary of configuration options for the Gunicorn server.

        """
        self.options = options or {}
        self.application = application
        self.stop_event = self.options.pop('stop_event', None)
        super().__init__()

    def load_config(self):
        """ Load the configuration to the app """
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        """ return the app """
        return self.application

class FlaskManager(LogBase):
    """
    FlaskManager is a class that manages the lifecycle of a Flask application.
    It provides methods to start and stop the Flask server using Gunicorn.
    """
    def __init__(self, ipc_manager: IPCManager):
        """
        Initialize the FlaskManager instance.

        Args:
            multiprocess_event (multiprocessing.Event): An event object used for inter-process communication.
        """

        self.registry = PluginRegistry(ipc_manager)
        self.blueprints = [ plugin.blueprint for plugin in self.registry.get_plugins_by_vertical(PluginVertical.BLUEPRINT) ]

        self.server: GunicornServer | None = None
        self.process: multiprocessing.Process | None = None

        config: Config = Config()
        self.host = config.server_host
        self.port = config.server_port

    @property
    def url(self):
        """ Return the network url """
        return get_network_url()

    @property
    def flask_app(self):
        return assemble_flask_server(self.blueprints, self.registry.ipc_manager)

    def start(self):
        """ Start the server """
        if self.process:
            self.logs.info("Server is already running.")
            return

        def stop(server):
            """ Inner stop for the server """
            self.registry.ipc_manager.stop_flag.set()
            self.process = None
            self.logs.info("Gunicorn Server 'on_exit' hooked. IPC.Event.set() done.")

        options = {
            'bind': f'{self.host}:{self.port}',
            'workers': 4,
            'worker_class': 'sync',
            'threads': multiprocessing.cpu_count() * 2,
            'on_exit': stop,
        }

        self.server = GunicornServer(self.flask_app, options)

        self.process = multiprocessing.Process(target=self.server.run)
        self.process.start()
        self.logs.info(f"GUincorn Server started in seperate process: {self.url}")

    def stop(self):
        """ Stop the server """
        if self.process:
            self.logs.info("AMI Flask server stopped!")
            self.process.terminate()
            self.process.join()
