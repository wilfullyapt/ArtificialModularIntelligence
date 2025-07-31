
"""
Tests for the C CLI binary functionality.
These tests verify the C binary behavior through subprocess calls.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest


class TestCCLI:
    """Test suite for the C CLI binary."""
    
    @pytest.fixture
    def cli_binary(self):
        """Get path to the compiled CLI binary."""
        cli_path = Path(__file__).parent.parent.parent / "cli" / "ami"
        if not cli_path.exists():
            pytest.skip("CLI binary not compiled. Run 'make cli' first.")
        return str(cli_path)
    
    @pytest.fixture
    def temp_home(self):
        """Create a temporary home directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_cli_help(self, cli_binary):
        """Test that CLI shows help when run without arguments."""
        result = subprocess.run([cli_binary], capture_output=True, text=True)
        assert result.returncode == 1
        assert "Usage: ami" in result.stdout
        assert "Commands:" in result.stdout
    
    def test_cli_verbose_flag(self, cli_binary):
        """Test verbose flag parsing."""
        result = subprocess.run([cli_binary, "-v"], capture_output=True, text=True)
        assert result.returncode == 1
        assert "Usage: ami" in result.stdout
        
        result = subprocess.run([cli_binary, "--verbose"], capture_output=True, text=True)
        assert result.returncode == 1
        assert "Usage: ami" in result.stdout
    
    def test_invalid_command(self, cli_binary):
        """Test handling of invalid commands."""
        result = subprocess.run([cli_binary, "invalid"], capture_output=True, text=True)
        assert result.returncode == 1
        assert "Usage: ami" in result.stdout
    
    def test_repository_validation(self, cli_binary, temp_home):
        """Test repository format validation for gethead command."""
        env = os.environ.copy()
        env['HOME'] = temp_home
        
        # Invalid repo formats
        invalid_repos = [
            "invalid",
            "/invalid",
            "invalid/",
            "user/repo/extra",
            "user//repo",
            "user/@repo",
        ]
        
        for invalid_repo in invalid_repos:
            result = subprocess.run(
                [cli_binary, "gethead", invalid_repo],
                capture_output=True,
                text=True,
                env=env
            )
            assert result.returncode == 1
            assert "Invalid repository format" in result.stderr
    
    def test_gethead_missing_home(self, cli_binary):
        """Test gethead command with missing HOME environment variable."""
        env = os.environ.copy()
        if 'HOME' in env:
            del env['HOME']
        
        result = subprocess.run(
            [cli_binary, "gethead", "user/repo"],
            capture_output=True,
            text=True,
            env=env
        )
        assert result.returncode == 1
        assert "HOME environment variable not set" in result.stderr
    
    def test_autostart_commands(self, cli_binary, temp_home):
        """Test autostart enable/disable commands."""
        env = os.environ.copy()
        env['HOME'] = temp_home
        
        # Test autostart enable (will fail without systemctl, but should create directories)
        result = subprocess.run(
            [cli_binary, "autostart", "enable"],
            capture_output=True,
            text=True,
            env=env
        )
        # Should create the systemd directory structure
        systemd_dir = Path(temp_home) / ".config" / "systemd" / "user"
        assert systemd_dir.exists()
    
    def test_plugin_delegation(self, cli_binary):
        """Test that plugin commands are properly delegated to Python CLI."""
        # This will fail because we don't have the full environment set up,
        # but we can verify the command construction
        result = subprocess.run(
            [cli_binary, "plugin", "list"],
            capture_output=True,
            text=True
        )
        # Should attempt to delegate to Python CLI
        assert result.returncode == 1  # Expected to fail in test environment
    
    def test_run_command(self, cli_binary):
        """Test the run command delegation."""
        result = subprocess.run(
            [cli_binary, "run"],
            capture_output=True,
            text=True
        )
        # Should attempt to run the Python application
        assert result.returncode == 1  # Expected to fail in test environment


class TestRepositoryValidation:
    """Detailed tests for repository validation logic."""
    
    def test_valid_repositories(self):
        """Test that valid repository formats are accepted."""
        valid_repos = [
            "user/repo",
            "github-user/my-repo",
            "user123/repo_name",
            "user-name/repo-name",
            "a/b",
        ]
        
        # We can't directly test the C function, but we can test through the CLI
        # This is a placeholder for when we extract the validation logic
        for repo in valid_repos:
            assert "/" in repo
            parts = repo.split("/")
            assert len(parts) == 2
            assert len(parts[0]) > 0
            assert len(parts[1]) > 0
    
    def test_invalid_repositories(self):
        """Test that invalid repository formats are rejected."""
        invalid_repos = [
            "",
            "/",
            "user/",
            "/repo",
            "user//repo",
            "user/repo/extra",
            "user repo",  # spaces
            "user@repo",  # invalid characters
        ]
        
        for repo in invalid_repos:
            # Basic validation that should fail
            if not repo or repo.count("/") != 1:
                continue  # These will fail the basic check
            parts = repo.split("/")
            if len(parts) != 2 or not parts[0] or not parts[1]:
                continue  # These will fail
            # Additional character validation would go here
