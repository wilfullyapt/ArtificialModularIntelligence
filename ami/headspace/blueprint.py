""" Blueprint Abstract Class definition """
from pathlib import Path
from sys import modules as sys_modules
from typing import Any, Callable, List, Literal, Optional
from multiprocessing.connection import Connection
import pickle

from flask import Blueprint as FlaskBlueprint, render_template as flask_render_template
from pydantic import BaseModel

from ami.headspace.base import Payload, Primitive

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

class MenuItem(BaseModel):
    """ Side Menu selections for AMI Blueprint page inegration """
    name: str
    url: str

class HeaderButton(BaseModel):
    """ Header item for AMI Blueprint page inegration """
    form: str
    value: str

class TemplateSettings(BaseModel):
    """ Template settings for AMI Blueprint page inegration """
    headspace: str
    title: str
    header: str
    css: Optional[str] = None
    js: Optional[str] = None
    buttons: List[HeaderButton] = []
    menu_items: List[MenuItem] = []

    def augment(self, **kwargs: Any) -> 'TemplateSettings':
        """ Augement setting without changing the settings """
        data = self.asdict()
        for key, value in kwargs.items():
            if key in data:
                data[key] = value
        return TemplateSettings(**data)

    def asdict(self):
        """ Get settings as a dictionary """
        return self.model_dump()

def render_template(template_name, tempsets: TemplateSettings, *args, **kwargs):
    """ AMI Blueprint implementation for Flask.render_template """
    base_temp_settings = tempsets.asdict()
    base_temp_settings['content'] = flask_render_template(template_name, *args, **kwargs)
    return flask_render_template('base.html', **base_temp_settings)

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

    def __init__(self, pipe: Connection, *args, **kwargs):
        module_name = self.__class__.__name__
        class_module = self.__module__
        self._module_dir = get_path_from_class_module(class_module)
        FlaskBlueprint.__init__(self,
                                module_name,
                                class_module,
                                static_folder=self._module_dir/"static",
                                static_url_path=f"/{module_name.lower()}",
                                template_folder=self._module_dir/"templates",
                                *args,
                                **kwargs
                               )
        Primitive.__init__(self)


        self.pipe: Connection = pipe

        for _, method in self._routes:
            route, methods = method._route
            self.route(route, methods=methods)(method.__get__(self, self.__class__))

        self._template_settings = TemplateSettings(
            headspace=module_name,
            title=f"{module_name} Headspace",
            header=f"{module_name} Blueprint"
        )

    def __repr__(self) -> str:
        return f"<AMI.headspace.Blueprint('{self.name}') package='{self.__module__}'>"

    def reload_gui(self):
        """ Given reload GUI call for subclasses """
        reloader = Payload.reload(module_name=self.name.lower())
        pickled_payload = pickle.dumps(reloader)
        self.pipe.send(pickled_payload)

    @property
    def tempsets(self):
        """ Template Setting property """
        return self._template_settings

    def update_tempsets(self, **kwargs):
        """ Template setting augementer """
        self._template_settings = self.tempsets.augment(**kwargs)
