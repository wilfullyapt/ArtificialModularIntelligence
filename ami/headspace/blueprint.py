""" Blueprint Abstract Class definition """
from functools import cached_property, wraps
from pathlib import Path
from sys import modules as sys_modules
from typing import Any, Callable, Dict, List, Literal, Tuple

from flask import Blueprint as FlaskBlueprint, render_template
from pydantic import BaseModel

from ..ipc import IPCManager
from ..headspace import Primitive

def get_path_from_class_module(class_module: str) -> Path:
    """ Returns the parent module path for a child module """
    module = '.'.join(class_module.split('.')[:-1])
    return Path(sys_modules[module].__path__[0])

HTTPMethod = Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
def route(route: str, methods: List[str] = ['GET']):
    """ Route decorator for AMI routes contained in the AMI Blueprint subclass """
    def decorator(func: Callable):
        func._route = (route, methods)
        return func
    return decorator

def plugin_template(template_name, **kwargs) -> Tuple[str, Dict[str, Any]]:
    return template_name, kwargs

class HeaderButton(BaseModel):
    """ Header item for AMI Blueprint page inegration """
    form: str
    value: str

class BlueprintMeta(type):
    """ Blueprint metaclass for routing purposes """
    def __new__(cls, name, bases, attrs):
        routes = []
        for key, value in attrs.items():
            if hasattr(value, '_route'):
                routes.append((key, value))
        attrs['_routes'] = routes
        return super().__new__(cls, name, bases, attrs)

class Blueprint(FlaskBlueprint, Primitive, metaclass=BlueprintMeta):
    """
    Custom Blueprint class combining Flask's Blueprint functionality with AMI-specific features.

    This class extends Flask's Blueprint and includes additional routing capabilities,
    template settings management, and inter-process communication through a pipe.

    Attributes:
        pipe (Connection): A multiprocessing connection for inter-process communication.
        _module_dir (Path): The directory path of the module containing this Blueprint.
        _template_settings (TemplateSettings): Settings for rendering templates.

    The class uses a metaclass (BlueprintMeta) to handle route definitions and
    provides methods for reloading the GUI and managing template settings.
    """

    def __init__(self, ipc_manager: IPCManager, *args, **kwargs):
        module_name = self.__class__.__name__
        class_module = self.__module__
        self._module_dir = get_path_from_class_module(class_module)
        FlaskBlueprint.__init__(self,
                                module_name,
                                class_module,
                                static_folder=self._module_dir/"static",
                                static_url_path=f"/{self._module_dir.name}",
                                template_folder=self._module_dir/"templates",
                                url_prefix=f"/{self._module_dir.name}",
                                *args,
                                **kwargs
                               )
        self.logs.debug(f"Blueprint for {module_name} loaded with static_folder={self._module_dir}/static")
        self.logs.debug(f"Blueprint for {module_name} loaded with static_url_path=/{self._module_dir.name}")
        self.logs.debug(f"Blueprint for {module_name} loaded with template_folder={self._module_dir}/templates")
        self.logs.debug(f"Blueprint for {module_name} loaded with url_prefix=/{self._module_dir.name}")

        self.ipc_manager: IPCManager = ipc_manager

        for _, method in self._routes:
            route, methods = method._route
            bound_method = method.__get__(self, self.__class__)
            wrapped_method = self.router_wrapper(bound_method)
            self.route(route, methods=methods)(wrapped_method)

    def router_wrapper(self, func: Callable) -> Callable:
        """Wraps route functions to handle rendering within base.html or pass through other responses."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
                template_name, blueprint_context = result
                rendered_blueprint = render_template(template_name, **blueprint_context)
                
                context = self.template_context
                context.update(blueprint_context.pop("context_overides", {}))
                context.update(blueprint_context.pop("buttons", {}))

                print("Context:")
                print(context)

                return render_template('base.html', content=rendered_blueprint, **context)

            return result
        return wrapper

    @cached_property
    def template_context(self):
        return {
            "title": self.name.capitalize(),
            "header": f"{self.name.capitalize()} Headspace"
        }

    def __repr__(self) -> str:
        return f"<AMI.headspace.Blueprint('{self.name}') package='{self.__module__}'>"

    def reload_gui(self, module_name=None):
        """ Given reload GUI call for subclasses """
        if not module_name:
            module_name = self.name.lower()
            self.logs.info(f"Reload GUI called for {module_name}")

