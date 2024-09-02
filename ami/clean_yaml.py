import yaml
from pathlib import Path
from typing import Any, Union

class YamlDict(dict):
    def __init__(self, data, local_config):
        self.local_config = local_config
        super().__init__(data)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.local_config.save()

    def __getitem__(self, key):
        value = super().__getitem__(key)
        if isinstance(value, dict):
            return YamlDict(value, self.local_config)
        elif isinstance(value, list):
            return YamlList(value, self.local_config)
        return value

class YamlList(list):
    def __init__(self, lst, local_config):
        self.local_config = local_config
        super().__init__(lst)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.local_config.save()

    def append(self, value):
        super().append(value)
        self.local_config.save()

    def extend(self, iterable):
        super().extend(iterable)
        self.local_config.save()

    def pop(self, index=-1):
        value = super().pop(index)
        self.local_config.save()
        return value

    def remove(self, value):
        super().remove(value)
        self.local_config.save()

def _load_yaml(yaml_path):
    with open(yaml_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

class LocalConfig:
    def __init__(self, yaml_path: Union[str, Path]):
        self._yaml_path = Path(yaml_path)
        self._yaml = _load_yaml(self._yaml_path)

    def save(self):
        with open(self._yaml_path, 'w') as file:
            yaml.dump(self._yaml, file)

    def __getitem__(self, key: str) -> Any:
        if key in self._yaml:
            value = self._yaml[key]
            if isinstance(value, dict):
                return YamlDict(value, self)
            elif isinstance(value, list):
                return YamlList(value, self)
            return value
        raise KeyError(f"'{key}' not found in config")

    def __setitem__(self, key: str, value: Any) -> None:
        self._yaml[key] = value
        self.save()
