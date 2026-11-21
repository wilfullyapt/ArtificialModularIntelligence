""" Manager for the Flask Server """

import multiprocessing
import socket

from ..core import Config, LogBase, PluginRegistry, PluginVertical
from ..ipc import IPCManager

from .gunicorn_opts import resolve_gunicorn_options
from .server import assemble_flask_server


def get_network_url(remote_host="www.x.com"):
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


class FlaskManager(LogBase):
    def __init__(self, ipc_manager: IPCManager):
        self.registry = PluginRegistry(ipc_manager)
        self.blueprints = [
            plugin.blueprint for plugin in self.registry.get_plugins_by_vertical(PluginVertical.BLUEPRINT)
        ]
        self.server = None
        self.process: multiprocessing.Process | None = None
        config: Config = Config()
        self.host = config.server_host
        self.port = config.server_port

    @property
    def url(self):
        return get_network_url()

    @property
    def flask_app(self):
        return assemble_flask_server(self.blueprints, self.registry.ipc_manager)

    def start(self):
        if self.process:
            self.logs.info("Server is already running.")
            return

        from gunicorn.app.base import BaseApplication

        class GunicornServer(BaseApplication):
            def __init__(self, application, options=None):
                self.options = options or {}
                self.application = application
                self.stop_event = self.options.pop("stop_event", None)
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    if key in self.cfg.settings and value is not None:
                        self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        opts = resolve_gunicorn_options()
        kill_on_exit = opts.pop("kill_ami_on_exit")

        def on_exit(server):
            self.logs.info("Gunicorn Server on_exit hooked.")
            if kill_on_exit:
                try:
                    self.registry.ipc_manager.stop_flag.set()
                    self.logs.warning("server.kill_ami_on_exit=true → IPC stop_flag set")
                except Exception as exc:
                    self.logs.error(f"Failed to set stop_flag: {exc}")
            self.process = None

        options = {
            "bind": f"{self.host}:{self.port}",
            "workers": opts["workers"],
            "worker_class": "sync",
            "threads": opts["threads"],
            "on_exit": on_exit,
        }

        self.server = GunicornServer(self.flask_app, options)
        self.process = multiprocessing.Process(target=self.server.run)
        self.process.start()
        self.logs.info(
            f"Gunicorn started ({opts['workers']}w/{opts['threads']}t): {self.url}"
        )

    def stop(self):
        if self.process:
            self.logs.info("AMI Flask server stopped!")
            self.process.terminate()
            self.process.join()
