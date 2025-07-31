
"""
Tests for the Python CLI functionality in ami/cli.py
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from ami.cli import AMICLIManager, main, handle_plugin_command, handle_update_command
from ami.core.registry import ComponentStatus


class TestAMICLIManager:
    """Test suite for AMICLIManager class."""
    
    @pytest.fixture
    def temp_config(self):
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'enabled_headspaces': ['corespace', 'markdown'],
                'ai': {'provider': 'openai'},
                'flask': {'port': 58744}
            }
            yaml.safe_dump(config_data, f)
            yield f.name
        Path(f.name).unlink()
    
    @pytest.fixture
    def cli_manager(self, temp_config):
        """Create a CLI manager instance for testing."""
        with patch('ami.cli.Config') as mock_config:
            mock_config.return_value.ami_config_filepath = temp_config
            mock_config.return_value.enabled_plugins = ['corespace', 'markdown']
            
            with patch('ami.cli.IPCManager'), patch('ami.cli.PluginRegistry'):
                manager = AMICLIManager()
                return manager
    
    def test_cli_manager_initialization(self):
        """Test that CLI manager initializes correctly."""
        with patch('ami.cli.Config'), patch('ami.cli.IPCManager'), patch('ami.cli.PluginRegistry'):
            manager = AMICLIManager()
            assert hasattr(manager, 'config')
            assert hasattr(manager, 'ipc_manager')
            assert hasattr(manager, 'registry')
    
    def test_list_plugins(self, cli_manager, capsys):
        """Test plugin listing functionality."""
        # Mock plugin data
        mock_plugin = Mock()
        mock_plugin.name = "test-plugin"
        mock_plugin.version = "1.0.0"
        mock_plugin.status = ComponentStatus.ACTIVE
        
        cli_manager.registry.plugin_cache = {"test-plugin": mock_plugin}
        
        cli_manager.list_plugins()
        
        captured = capsys.readouterr()
        assert "Available Plugins:" in captured.out
        assert "test-plugin" in captured.out
        assert "1.0.0" in captured.out
        assert "✓" in captured.out
    
    def test_plugin_status_found(self, cli_manager, capsys):
        """Test plugin status for existing plugin."""
        mock_plugin = Mock()
        mock_plugin.name = "test-plugin"
        mock_plugin.version = "1.0.0"
        mock_plugin.status = ComponentStatus.ACTIVE
        mock_plugin.location = "/path/to/plugin"
        mock_plugin.repo_url = "https://github.com/user/repo"
        mock_plugin.gui = True
        mock_plugin.headspace = True
        mock_plugin.blueprint = False
        
        cli_manager.registry.__getitem__ = Mock(return_value=mock_plugin)
        
        cli_manager.plugin_status("test-plugin")
        
        captured = capsys.readouterr()
        assert "Plugin: test-plugin" in captured.out
        assert "Version: 1.0.0" in captured.out
        assert "Components: GUI, Headspace" in captured.out
    
    def test_plugin_status_not_found(self, cli_manager, capsys):
        """Test plugin status for non-existent plugin."""
        cli_manager.registry.__getitem__ = Mock(return_value=None)
        
        cli_manager.plugin_status("nonexistent")
        
        captured = capsys.readouterr()
        assert "Plugin 'nonexistent' not found" in captured.out
    
    def test_enable_plugin_success(self, cli_manager, temp_config, capsys):
        """Test successful plugin enabling."""
        mock_plugin = Mock()
        mock_plugin.name = "test-plugin"
        mock_plugin.status = ComponentStatus.DISABLED
        
        cli_manager.registry.__getitem__ = Mock(return_value=mock_plugin)
        cli_manager.config.enabled_plugins = []
        cli_manager.config.ami_config_filepath = temp_config
        
        with patch.object(cli_manager, '_update_config_enabled_plugins') as mock_update:
            cli_manager.enable_plugin("test-plugin")
        
        mock_update.assert_called_once_with(["test-plugin"])
        captured = capsys.readouterr()
        assert "Plugin 'test-plugin' enabled" in captured.out
    
    def test_enable_plugin_already_enabled(self, cli_manager, capsys):
        """Test enabling an already active plugin."""
        mock_plugin = Mock()
        mock_plugin.name = "test-plugin"
        mock_plugin.status = ComponentStatus.ACTIVE
        
        cli_manager.registry.__getitem__ = Mock(return_value=mock_plugin)
        
        cli_manager.enable_plugin("test-plugin")
        
        captured = capsys.readouterr()
        assert "Plugin 'test-plugin' is already enabled" in captured.out
    
    def test_disable_plugin_success(self, cli_manager, temp_config, capsys):
        """Test successful plugin disabling."""
        mock_plugin = Mock()
        mock_plugin.name = "test-plugin"
        mock_plugin.status = ComponentStatus.ACTIVE
        
        cli_manager.registry.__getitem__ = Mock(return_value=mock_plugin)
        cli_manager.config.enabled_plugins = ["test-plugin", "other-plugin"]
        cli_manager.config.ami_config_filepath = temp_config
        
        with patch.object(cli_manager, '_update_config_enabled_plugins') as mock_update:
            cli_manager.disable_plugin("test-plugin")
        
        mock_update.assert_called_once_with(["other-plugin"])
        captured = capsys.readouterr()
        assert "Plugin 'test-plugin' disabled" in captured.out
    
    def test_update_config_enabled_plugins(self, cli_manager, temp_config):
        """Test configuration file updating."""
        cli_manager.config.ami_config_filepath = temp_config
        
        cli_manager._update_config_enabled_plugins(["plugin1", "plugin2"])
        
        # Read back the config to verify changes
        with open(temp_config, 'r') as f:
            config_data = yaml.safe_load(f)
        
        assert config_data['enabled_headspaces'] == ["plugin1", "plugin2"]


class TestCLIFunctions:
    """Test standalone CLI functions."""
    
    def test_handle_update_command(self, capsys):
        """Test update command handling."""
        with patch('ami.cli.UpdateManager') as mock_update_manager:
            mock_manager = mock_update_manager.return_value
            mock_manager.check_for_updates.return_value = {
                'message': 'No updates available',
                'update_available': False
            }
            
            mock_args = Mock()
            handle_update_command(mock_args)
            
            captured = capsys.readouterr()
            assert "Checking for updates..." in captured.out
            assert "No updates available" in captured.out
    
    def test_handle_update_command_with_updates(self, capsys):
        """Test update command when updates are available."""
        with patch('ami.cli.UpdateManager') as mock_update_manager:
            mock_manager = mock_update_manager.return_value
            mock_manager.check_for_updates.return_value = {
                'message': 'Updates available',
                'update_available': True
            }
            mock_manager.perform_update.return_value = {
                'success': True,
                'message': 'Update completed'
            }
            
            with patch('builtins.input', return_value='y'):
                mock_args = Mock()
                handle_update_command(mock_args)
            
            captured = capsys.readouterr()
            assert "Updates are available" in captured.out
            assert "Update completed successfully!" in captured.out


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    def test_main_function_plugin_list(self):
        """Test main function with plugin list command."""
        test_args = ['ami', 'plugin', 'list']
        
        with patch('sys.argv', test_args):
            with patch('ami.cli.AMICLIManager') as mock_manager:
                mock_instance = mock_manager.return_value
                
                with patch('ami.cli.argparse.ArgumentParser.parse_args') as mock_parse:
                    mock_args = Mock()
                    mock_args.command = 'plugin'
                    mock_args.plugin_action = 'list'
                    mock_parse.return_value = mock_args
                    
                    # This should not raise an exception
                    try:
                        main()
                    except SystemExit:
                        pass  # Expected for argument parser
    
    def test_main_function_plugin_enable(self):
        """Test main function with plugin enable command."""
        test_args = ['ami', 'plugin', 'enable', 'test-plugin']
        
        with patch('sys.argv', test_args):
            with patch('ami.cli.AMICLIManager') as mock_manager:
                mock_instance = mock_manager.return_value
                
                with patch('ami.cli.argparse.ArgumentParser.parse_args') as mock_parse:
                    mock_args = Mock()
                    mock_args.command = 'plugin'
                    mock_args.plugin_action = 'enable'
                    mock_args.name = 'test-plugin'
                    mock_parse.return_value = mock_args
                    
                    try:
                        main()
                    except SystemExit:
                        pass  # Expected for argument parser


@pytest.fixture
def mock_environment():
    """Create a controlled environment for testing."""
    with patch.dict('os.environ', {'HOME': '/tmp/test_home'}):
        yield


class TestCLIErrorHandling:
    """Test error handling scenarios."""
    
    def test_ipc_failure_handling(self, cli_manager):
        """Test graceful handling of IPC failures."""
        mock_plugin = Mock()
        mock_plugin.name = "test-plugin"
        mock_plugin.status = ComponentStatus.DISABLED
        
        cli_manager.registry.__getitem__ = Mock(return_value=mock_plugin)
        cli_manager.config.enabled_plugins = []
        
        # Mock IPC manager to raise exception
        cli_manager.ipc_manager.send_event = Mock(side_effect=Exception("IPC failed"))
        
        with patch.object(cli_manager, '_update_config_enabled_plugins'):
            # Should not raise exception despite IPC failure
            cli_manager.enable_plugin("test-plugin")
    
    def test_config_file_not_found(self):
        """Test handling of missing config file."""
        with patch('ami.cli.Config') as mock_config:
            mock_config.return_value.ami_config_filepath = "/nonexistent/config.yaml"
            
            with patch('ami.cli.IPCManager'), patch('ami.cli.PluginRegistry'):
                manager = AMICLIManager()
                
                # Should handle missing config file gracefully
                with pytest.raises(FileNotFoundError):
                    manager._update_config_enabled_plugins(["test"])
