""" Manager for the Flask Server """

import multiprocessing
from typing import List, Type
import socket

from gunicorn.app.base import BaseApplication

from ami.base import Base
from ami.config import Config
from ami.core.headspace_importer import import_headspace
from ami.interfaces.web.server import create_app

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

def is_valid_ip(ip_str: str):
    """ Validate the IP """
    ip_parts = ip_str.split('.')
    if len(ip_parts) != 4:
        return False
    for part in ip_parts:
        if not part.isdigit() or int(part) < 0 or int(part) > 255:
            return False
    return True

def is_valid_port(port: int):
    """ Validate the port """
    return isinstance(port, int) and 0 < port < 65536

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

    def init(self, parser, opts, args):
        """
        Initialize the Gunicorn application.

        This method is required to be implemented as it's an abstract method in BaseApplication.
        """
        pass

    def load_config(self):
        """ Load the configuration to the app """
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        """ return the app """
        return self.application

class FlaskManager(Base):
    """
    FlaskManager is a class that manages the lifecycle of a Flask application.
    It provides methods to start and stop the Flask server using Gunicorn.
    """
    def __init__(self):
        """
        Initialize the FlaskManager instance.

        Args:
            multiprocess_event (multiprocessing.Event): An event object used for inter-process
                                                        communication.
        """
        super().__init__()

        self.stop_event = multiprocessing.Event()
        self.server: GunicornServer | None = None
        self.process: multiprocessing.Process | None = None
        self.pipe: multiprocessing.connection.Connection | None = None

        config: Config = Config()
        self.host = config.get('host')
        self.port = config.get('port')

    @property
    def url(self):
        """ Return the network url """
        return get_network_url()

    def run_server(self, blueprints, pipe: multiprocessing.connection.Connection):
        """Function to run in the child process"""
        app = create_app()

        for bp in blueprints:
            app.register_blueprint(bp(pipe))

        options = {
            'bind': f'{self.host}:{self.port}',
            'workers': 4,
            'worker_class': 'sync',
            'threads': multiprocessing.cpu_count() * 2,
            'stop_event': self.stop_event
        }

        server = GunicornServer(app, options)
        server.run()

    def spawn_server_process(self, headspaces):
        """Start the server in a new process"""
        if self.process:
            self.logs.info("Server is already running.")
            return

        self.pipe, child_conn = multiprocessing.Pipe()

        blueprints = { headspace_name: import_headspace(headspace_name, extract='blueprint') for headspace_name in headspaces }
        blueprints = [ getattr(module, name.capitalize()) for name, module in blueprints.items() if hasattr(module, name.capitalize()) ]
        self.process = multiprocessing.Process(target=self.run_server, args=(blueprints, child_conn))
        self.process.start()
        self.logs.info(f"Gunicorn Server started in separate process: {self.url}")

    def send_to_server(self, message):
        """Send message from GUI to server"""
        if self.pipe:
            self.pipe.send(message)

    def receive_from_server(self):
        """Receive message from server (non-blocking)"""
        if self.pipe and self.pipe.poll():  # Check if message available
            return self.pipe.recv()
        return None

    def stop(self):
        """Stop the server"""
        if self.process:
            self.stop_event.set()
            self.process.terminate()
            self.process.join()
            if self.pipe:
                self.pipe.close()
                self.pipe = None
