""" The main attraction """
import sys
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from types import ModuleType
from typing import Optional

from ami.config import Config

logs = Config().load_blank_logging()
logs(__file__)

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

def import_headspace(headspace_name: str, extract: Optional[str]=None) -> Optional[ModuleType]:

    module_name = f"ami.imported_headspaces.{headspace_name}"

    if module_name in sys.modules:
        module = sys.modules[module_name]
        if extract is not None:
            return getattr(module, extract, None)
        return module

    module_path = Config().modules_dir / headspace_name / "__init__.py"
    if module_path.exists() and module_path.is_file():
        module = load_module(module_name, module_path)
        if module is None:
            return None

        module.__path__ = [str(module_path.parent)]
        load_submodules(module, module_path.parent)

        if extract is not None:
            return getattr(module, extract, None)

        return module

    return None
