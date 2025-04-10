""" The main attraction """
import sys
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from types import ModuleType
from typing import Optional

from ami.core import Config, Logger

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

def import_headspace(headspace_name: str, extract: Optional[str]=None) -> Optional[ModuleType]:
    modules_dir = Config().modules_dir
    print(f"__name__: {__name__}")
    print(f"__package__: {__package__}")
    base_package = "ami.imported_headspaces"
    if base_package not in sys.modules:
        base_init = modules_dir / "__init__.py"
        if base_init.exists() and base_init.is_file():
            base_module = load_module(base_package, base_init)
            if base_module is not None:
                base_module.__path__ = [str(modules_dir)]
                sys.modules[base_package] = base_module

    module_name = f"ami.imported_headspaces.{headspace_name}"

    if module_name in sys.modules:
        module = sys.modules[module_name]
        if extract is not None:
            return getattr(module, extract, None)
        return module

    module_path = modules_dir / headspace_name / "__init__.py"
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
