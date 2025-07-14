"""Main importing script. Used for builtins and 3rd party plugins"""
import sys
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from types import ModuleType
from typing import Optional

from ..core import Config, Logger

logs = Logger(Config().log_config)("ami.core.headspace_importer")

def load_module(name: str, path: Path) -> Optional[ModuleType]:
    if not path.exists():
        return None
    try:
        spec = spec_from_file_location(name, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module {name} from {path}")
        module = module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    except ImportError as e:
        import traceback
        logs.error(f"Failed to import {name}: {e}")
        logs.error(traceback.format_exc())
        return None

def load_submodules(module: ModuleType, base_path: Path) -> None:
    """ Load all Python files in the module directory as submodules. """
    if not hasattr(module, '__path__'):
        return

    for py_file in base_path.glob('*.py'):
        if py_file.name == '__init__.py':
            continue

        submodule_name = f"{module.__name__}.{py_file.stem}"
        submodule = load_module(submodule_name, py_file)
        if submodule is not None:
            setattr(module, py_file.stem, submodule)
            logs.info(f"Submodule for {module.__name__}, {submodule.__name__}, has been added")

def import_plugin(dirpath: Path) -> Optional[ModuleType]:
    """Import a plugin from a directory path and return its package name."""
    if not dirpath.is_dir():
        raise NotADirectoryError(f"Not a directory: {dirpath}")
    if not (dirpath / "__init__.py").exists():
        raise FileNotFoundError(f"No __init__.py found in package {dirpath}")
        
    package_name = dirpath.name
    module_name = f"ami.__plugin__.{package_name}"
    
    # Create the base __plugin__ package if it doesn't exist
    base_package = "ami.__plugin__"
    if base_package not in sys.modules:
        sys.modules[base_package] = ModuleType(base_package)
        sys.modules[base_package].__path__ = []
    
    # Import the plugin module
    init_path = dirpath / "__init__.py"
    module = load_module(module_name, init_path)
    
    if module is not None:
        module.__path__ = [str(dirpath)]
        load_submodules(module, dirpath)
        return module
        
    return None
