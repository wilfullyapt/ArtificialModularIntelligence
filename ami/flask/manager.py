""" Manager for the Flask Server """

import multiprocessing
from typing import List, Type
import socket

from gunicorn.app.base import BaseApplication

from ami.base import Base
from ami.config import Config

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

def get_network_url_depricated():
    """ get the ip address and port for the hosted flask server """
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    port = Config().server_port
    return f"{ip_address}:{port}"

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
    def __init__(self, multiprocess_event: multiprocessing.Event):
        """
        Initialize the FlaskManager instance.

        Args:
            multiprocess_event (multiprocessing.Event): An event object used for inter-process
                                                        communication.
        """
        super().__init__()

        self.stop_event: multiprocessing.Event = multiprocess_event
        self.server: GunicornServer | None = None
        self.process: multiprocessing.Process | None = None

        config: Config = Config()
        self.host = config.get('host')
        self.port = config.get('port')

    @property
    def url(self):
        """ Return the network url """
        return get_network_url_rpi()

    def start(self, flask_app):
        """ Start the server """
        if self.process:
            self.logs.info("Server is already running.")
            return

        def stop(server):
            """ Inner stop for the server """
            self.stop_event.set()
            self.process = None
            self.logs.info("Gunicorn Server 'on_exit' hooked. IPC.Event.set() done.")

        options = {
            'bind': f'{self.host}:{self.port}',
            'workers': 4,
            'worker_class': 'sync',
            'threads': multiprocessing.cpu_count() * 2,
            'on_exit': stop,
        }

        self.server = GunicornServer(flask_app, options)

        self.process = multiprocessing.Process(target=self.server.run)
        self.process.start()
        self.logs.info("GUincorn Server started in seperate process.")

    def stop(self):
        """ Stop the server """
        if self.process:
            self.process.terminate()
            self.process.join()

def create_flask_app(blueprints: List[Type], pipe: multiprocessing.connection.Connection):
    """ Create and return the app """
    from .server import app

    for bp in blueprints:
        app.register_blueprint(bp(pipe))

    return app
