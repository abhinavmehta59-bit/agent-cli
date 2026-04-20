"""Tests for agent-cli."""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add agent_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestIsRunning:
    """Test is_running function."""
    
    def test_stale_pid_file(self, tmp_path):
        """Test cleans up stale PID file."""
        from agent_cli import __main__
        
        pid_file = tmp_path / "stale.pid"
        pid_file.write_text("999999")  # Non-existent PID
        
        with patch.object(__main__, 'CONFIG_DIR', tmp_path):
            with patch.object(__main__, 'PID_DIR', tmp_path):
                result = __main__.is_running("stale")
                assert result is False
                # PID file should be cleaned up
                assert not pid_file.exists()


class TestLoadTemplates:
    """Test load_templates function."""
    
    def test_load_templates_nested(self):
        """Test loading templates with nested structure."""
        from agent_cli.__main__ import load_templates
        templates = load_templates()
        
        assert "email-agent" in templates
        assert "social-agent" in templates
        assert "research-agent" in templates
        assert "full-stack" in templates
    
    def test_template_structure(self):
        """Test template has required fields."""
        from agent_cli.__main__ import load_templates
        templates = load_templates()
        
        email = templates["email-agent"]
        assert "name" in email
        assert "required_skills" in email
        assert "required_tools" in email


class TestFindHermesBinary:
    """Test find_hermes_binary function."""
    
    def test_finds_hermes_in_venv(self):
        """Test finds hermes in common venv location."""
        from agent_cli.__main__ import find_hermes_binary
        
        result = find_hermes_binary()
        # Should find hermes in ~/.hermes/hermes-agent/venv/bin/hermes
        assert result is not None
        assert "hermes" in result


class TestCmdStart:
    """Test cmd_start function."""
    
    def test_start_missing_config(self, capsys):
        """Test start fails gracefully when no config exists."""
        from agent_cli.__main__ import cmd_start
        from argparse import Namespace
        
        with tempfile.TemporaryDirectory() as tmp:
            with patch('agent_cli.__main__.CONFIG_DIR', Path(tmp)):
                with patch('agent_cli.__main__.PID_DIR', Path(tmp) / "pids"):
                    with patch('agent_cli.__main__.LOG_DIR', Path(tmp) / "logs"):
                        with patch('agent_cli.__main__.find_hermes_binary', return_value="/bin/ls"):
                            with patch('agent_cli.__main__.load_templates', return_value={"test-agent": {}}):
                                args = Namespace(agent="test-agent")
                                result = cmd_start(args)
                                assert result == 1
                                captured = capsys.readouterr()
                                assert "no config found" in captured.out


class TestCmdStop:
    """Test cmd_stop function."""
    
    def test_stop_no_running_agents(self, capsys):
        """Test stop handles no running agents."""
        from agent_cli.__main__ import cmd_stop
        from argparse import Namespace
        
        with patch('agent_cli.__main__.load_templates', return_value={"test-agent": {}}):
            with patch('agent_cli.__main__.is_running', return_value=False):
                args = Namespace(agent="test-agent")
                result = cmd_stop(args)
                assert result == 0
                captured = capsys.readouterr()
                assert "No agents running" in captured.out


class TestCmdStatus:
    """Test cmd_status function."""
    
    def test_status_output_format(self, capsys):
        """Test status outputs correct format."""
        from agent_cli.__main__ import cmd_status
        from argparse import Namespace
        
        with patch('agent_cli.__main__.load_templates', return_value={
            "email-agent": {},
            "social-agent": {}
        }):
            with patch('agent_cli.__main__.is_running', return_value=False):
                args = Namespace()
                result = cmd_status(args)
                assert result == 0
                captured = capsys.readouterr()
                assert "STATUS DASHBOARD" in captured.out
                assert "email-agent" in captured.out
                assert "social-agent" in captured.out


class TestCmdMonitor:
    """Test cmd_monitor function."""
    
    def test_monitor_max_retries_tracking(self):
        """Test max retries are tracked per agent."""
        from agent_cli.__main__ import cmd_monitor
        from argparse import Namespace
        
        # Mock to run only one iteration
        with patch('agent_cli.__main__.load_templates', return_value={"test-agent": {}}):
            with patch('agent_cli.__main__.get_agent_config', return_value={}):
                with patch('agent_cli.__main__.is_running', return_value=False):
                    with patch('agent_cli.__main__.find_hermes_binary', return_value=None):
                        with patch('agent_cli.__main__.time.sleep', side_effect=KeyboardInterrupt):
                            args = Namespace(interval=1, no_restart=False, max_retries=3)
                            result = cmd_monitor(args)
                            assert result == 0
    
    def test_monitor_no_restart_flag(self, capsys):
        """Test monitor respects --no-restart flag."""
        from agent_cli.__main__ import cmd_monitor
        from argparse import Namespace
        
        with patch('agent_cli.__main__.load_templates', return_value={"test-agent": {}}):
            with patch('agent_cli.__main__.get_agent_config', return_value={}):
                with patch('agent_cli.__main__.is_running', return_value=False):
                    with patch('agent_cli.__main__.time.sleep', side_effect=KeyboardInterrupt):
                        args = Namespace(interval=1, no_restart=True, max_retries=3)
                        result = cmd_monitor(args)
                        assert result == 0
                        captured = capsys.readouterr()
                        assert "auto-restart: False" in captured.out


class TestBuildHermesCommand:
    """Test build_hermes_command function."""
    
    def test_builds_correct_command(self):
        """Test builds correct hermes command."""
        from agent_cli.__main__ import build_hermes_command, find_hermes_binary
        
        hermes = find_hermes_binary()
        config = {
            "default_config": {
                "auto_respond_enabled": True,
                "max_daily_emails": 100
            }
        }
        
        with patch('agent_cli.__main__.find_hermes_binary', return_value=hermes):
            cmd = build_hermes_command("email-agent", config)
            assert "gateway" in cmd
            assert "run" in cmd
            assert "--profile" in cmd
            assert "email-agent" in cmd


class TestIntegration:
    """Integration tests."""
    
    def test_cli_help(self):
        """Test CLI help works."""
        result = subprocess.run(
            [sys.executable, "-m", "agent_cli", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "Agent CLI" in result.stdout
        assert "start" in result.stdout
        assert "stop" in result.stdout
        assert "status" in result.stdout
    
    def test_cli_status_command(self):
        """Test status command runs."""
        result = subprocess.run(
            [sys.executable, "-m", "agent_cli", "status"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "STATUS DASHBOARD" in result.stdout
    
    def test_cli_monitor_help(self):
        """Test monitor command shows max-retries."""
        result = subprocess.run(
            [sys.executable, "-m", "agent_cli", "monitor", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "--max-retries" in result.stdout
        assert "-r" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])