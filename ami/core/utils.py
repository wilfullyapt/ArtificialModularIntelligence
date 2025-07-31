import json
import socket
from pathlib import Path
from typing import Dict, Any

from werkzeug.datastructures import ImmutableMultiDict
import yaml
from dotenv import load_dotenv, set_key

from ..core import LogBase, Config

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

class ConfigUpdater(LogBase):
    """ See `prod-hs-cli-features` branch for details about the setting editor from replit """
    def __init__(self):
        self.config = Config()

    def load_env_file(self) -> Dict[str, str]:
        """ Load environment variables from .env file """
        if not self.config.environment_file.exists():
            return {}
        
        load_dotenv(self.config.environment_file)
        env_vars = {}
        
        try:
            with open(self.config.environment_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip('"\'')
        except Exception as e:
            self.logs.error(f"Error loading .env file: {e}")
        
        return env_vars

    def load_ami_config(self) -> Dict[str, Any]:
        """Load AMI configuration from YAML file"""
        return self.config.dict

    def get_headspace_settings_files(self) -> Dict[str, Path]:
        """Get all headspace settings files"""
        config = Config()
        settings_files = {}
        
        # Check builtin headspaces
        for headspace_dir in config.builtin_plugins.iterdir():
            if headspace_dir.is_dir():
                settings_file = headspace_dir / "settings.json"
                if settings_file.exists():
                    settings_files[f"builtin_{headspace_dir.name}"] = settings_file
        
        # Check plugin headspaces
        for headspace_dir in config.plugins_dir.iterdir():
            if headspace_dir.is_dir():
                settings_file = headspace_dir / "settings.json"
                if settings_file.exists():
                    settings_files[f"plugin_{headspace_dir.name}"] = settings_file
        
        return settings_files

    def load_headspace_settings(self, settings_file: Path) -> Dict[str, Any]:
        """Load headspace settings from JSON file"""
        try:
            with open(settings_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logs.error(f"Error loading settings file {settings_file}: {e}")
            return {}

    def save_headspace_settings(self, settings_file: Path, settings_data: Dict[str, Any]):
        """Save headspace settings to JSON file"""
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings_data, f, indent=2)
        except Exception as e:
            self.logs.error(f"Error saving settings file {settings_file}: {e}")
            raise


    def save_env_file(self, form: ImmutableMultiDict) -> bool:
        env_vars = {}
        try:
            for key, value in form.items():
                if key.startswith('env_'):
                    env_key = key.replace('env_', '')
                    env_vars[env_key] = value

            with open(self.config.environment_file, 'w') as f:
                f.write("")             # Clear the file before rewriting it
            
            for key, value in env_vars.items():
                if key and value:
                    set_key(str(self.config.environment_file), key, value)

            return True

        except Exception as e:
            self.logs.error(f"Error saving AMI config: {e}")
            raise

    def save_ami_config(self, form: ImmutableMultiDict) -> bool:
        config_data = {}

        try:
            for key, value in form.items():
                if key.startswith('ami_config_'):
                    config_key = key.replace('ami_config_', '')

                    if value.lower() in ['true', 'false']:
                        config_data[config_key] = value.lower() == 'true'
                    elif value.isdigit():
                        config_data[config_key] = int(value)
                    elif config_key == 'enabled_headspaces':

                        config_data[config_key] = [item.strip() for item in value.split(',') if item.strip()]
                    else:
                        config_data[config_key] = value

            with open(self.config.ami_config_filepath, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)

            return True

        except Exception as e:
            self.logs.error(f"Error saving AMI config: {e}")
            raise

    def update_headspace_setting(self, items: Any):
        for key, value in items.items():
            if key.endswith('_submit'):
                headspace_name = key.replace('_submit', '')

        for key in items.keys():
            if key.endswith('_submit'):
                headspace_name = key.replace('_submit', '')
                settings_files = self.get_headspace_settings_files()

                if headspace_name in settings_files:
                    settings_data = {}
                    prefix = f"{headspace_name}_"

                    for form_key, value in items.items():
                        if form_key.startswith(prefix) and not form_key.endswith('_submit'):
                            setting_key = form_key.replace(prefix, '')
                            # Handle different data types
                            if value.lower() in ['true', 'false']:
                                settings_data[setting_key] = value.lower() == 'true'
                            elif value.isdigit():
                                settings_data[setting_key] = int(value)
                            else:
                                settings_data[setting_key] = value

                    self.save_headspace_settings(settings_files[headspace_name], settings_data)
                    print(f'{headspace_name} settings saved successfully!', 'success')
                break

