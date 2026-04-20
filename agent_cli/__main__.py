#!/usr/bin/env python3
"""
Agent CLI — Main entry point for managing AI agent workflows.
Target: Solo founders and small agencies.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Constants
CONFIG_DIR = Path.home() / ".hermes" / "agent-cli" / "config"
PID_DIR = CONFIG_DIR / "pids"
LOG_DIR = Path.home() / ".hermes" / "agent-cli" / "logs"

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
PID_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_templates() -> dict:
    """Load agent templates from JSON."""
    import importlib.resources as resources
    templates_file = resources.files("agent_cli").joinpath("templates.json")
    with templates_file.open() as f:
        data = json.load(f)
    # Handle both flat structure and nested {"templates": {...}} structure
    if "templates" in data:
        return data["templates"]
    return data


def get_agent_config(agent_name: str) -> Optional[dict]:
    """Load config for a specific agent."""
    config_file = CONFIG_DIR / f"{agent_name}.json"
    if not config_file.exists():
        return None
    with open(config_file) as f:
        return json.load(f)


def get_pid_file(agent_name: str) -> Path:
    """Get PID file path for an agent."""
    return PID_DIR / f"{agent_name}.pid"


def get_log_file(agent_name: str) -> Path:
    """Get log file path for an agent."""
    return LOG_DIR / f"{agent_name}.log"


def is_running(agent_name: str) -> bool:
    """Check if an agent is currently running."""
    pid_file = get_pid_file(agent_name)
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, 0)  # Check if process exists
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        # Process dead or no permission - clean up stale PID file
        pid_file.unlink(missing_ok=True)
        return False


def find_hermes_binary() -> Optional[str]:
    """Find the hermes binary."""
    # Check common venv locations first
    venv_paths = [
        Path.home() / ".hermes" / "hermes-agent" / "venv" / "bin" / "hermes",
    ]
    for path in venv_paths:
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    
    # Check PATH
    for path in os.environ.get("PATH", "").split(":"):
        binary = os.path.join(path, "hermes")
        if os.path.isfile(binary) and os.access(binary, os.X_OK):
            return binary
    # Check common locations
    common_paths = [
        "/usr/local/bin/hermes",
        "/opt/homebrew/bin/hermes",
        os.path.expanduser("~/.local/bin/hermes"),
    ]
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def build_hermes_command(agent_name: str, config: dict) -> list:
    """Build hermes gateway run command from config."""
    hermes_bin = find_hermes_binary()
    if not hermes_bin:
        raise RuntimeError("hermes binary not found. Install Hermes first.")
    
    cmd = [hermes_bin, "gateway", "run", "--profile", agent_name]
    
    # Add config overrides from agent config
    if "default_config" in config:
        for key, value in config["default_config"].items():
            cmd.extend([f"--{key}", str(value)])
    
    return cmd


def cmd_start(args) -> int:
    """Start one or all agents via Hermes gateway."""
    templates = load_templates()
    hermes_bin = find_hermes_binary()
    
    if not hermes_bin:
        print("❌ Hermes not found. Install from https://hermes.sh")
        return 1
    
    # Determine which agents to start
    if args.agent == "all":
        agents_to_start = list(templates.keys())
    else:
        if args.agent not in templates:
            print(f"❌ Unknown agent: {args.agent}")
            print(f"   Available: {', '.join(templates.keys())}")
            return 1
        agents_to_start = [args.agent]
    
    started = []
    failed = []
    
    for agent_name in agents_to_start:
        if is_running(agent_name):
            print(f"⏭️  {agent_name}: already running")
            continue
        
        config = get_agent_config(agent_name)
        if not config:
            print(f"⚠️  {agent_name}: no config found. Run setup-wizard.py first.")
            failed.append(agent_name)
            continue
        
        log_file = get_log_file(agent_name)
        
        try:
            # Build real hermes command
            cmd = build_hermes_command(agent_name, config)
            
            # Open log file for this agent
            log_fp = open(log_file, "a")
            
            # Start hermes gateway process
            proc = subprocess.Popen(
                cmd,
                stdout=log_fp,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            
            # Store PID
            pid_file = get_pid_file(agent_name)
            pid_file.write_text(str(proc.pid))
            
            # Record start time for uptime tracking
            start_time_file = CONFIG_DIR / f"{agent_name}.start_time"
            start_time_file.write_text(str(time.time()))
            
            print(f"✅ {agent_name}: started (PID {proc.pid})")
            print(f"   Command: {' '.join(cmd)}")
            print(f"   Logs: {log_file}")
            started.append(agent_name)
            
        except Exception as e:
            print(f"❌ {agent_name}: failed to start — {e}")
            failed.append(agent_name)
    
    print(f"\n📊 Started: {len(started)}, Failed: {len(failed)}")
    return 0 if not failed else 1


def cmd_stop(args) -> int:
    """Stop one or all agents."""
    templates = load_templates()
    
    if args.agent == "all":
        agents_to_stop = [k for k in templates.keys() if is_running(k)]
    else:
        agents_to_stop = [args.agent] if is_running(args.agent) else []
    
    if not agents_to_stop:
        print("No agents running.")
        return 0
    
    stopped = []
    for agent_name in agents_to_stop:
        pid_file = get_pid_file(agent_name)
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            # Force kill if still running
            try:
                os.kill(pid, 0)
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            pid_file.unlink(missing_ok=True)
            print(f"🛑 {agent_name}: stopped")
            stopped.append(agent_name)
        except Exception as e:
            print(f"❌ {agent_name}: {e}")
    
    print(f"\n📊 Stopped: {len(stopped)}")
    return 0


def cmd_status(args) -> int:
    """Show status dashboard for all agents."""
    templates = load_templates()
    
    print("\n" + "=" * 50)
    print("🤖 AGENT CLI — STATUS DASHBOARD")
    print("=" * 50)
    
    # Summary row
    running = sum(1 for k in templates.keys() if is_running(k))
    total = len(templates)
    print(f"\n📈 Running: {running}/{total} agents\n")
    
    # Agent details
    print(f"{'Agent':<20} {'Status':<12} {'PID':<10} {'Uptime'}")
    print("-" * 50)
    
    for agent_name in templates.keys():
        pid_file = get_pid_file(agent_name)
        log_file = get_log_file(agent_name)
        
        if is_running(agent_name):
            try:
                pid = int(pid_file.read_text().strip())
                # Get uptime from start_time file
                start_time_file = CONFIG_DIR / f"{agent_name}.start_time"
                uptime = "running"
                if start_time_file.exists():
                    try:
                        ts = float(start_time_file.read_text().strip())
                        secs = int(time.time() - ts)
                        mins = secs // 60
                        hours = mins // 60
                        if hours > 0:
                            uptime = f"{hours}h {mins%60}m"
                        elif mins > 0:
                            uptime = f"{mins}m"
                        else:
                            uptime = f"{secs}s"
                    except:
                        pass
                print(f"{agent_name:<20} {'🟢 running':<12} {pid:<10} {uptime}")
            except:
                print(f"{agent_name:<20} {'🟡 unknown':<12}")
        else:
            print(f"{agent_name:<20} {'⚪ stopped':<12}")
    
    print("-" * 50)
    
    # Quick actions hint
    print("\n💡 Commands:")
    print("   agent-cli.py start <agent>   — Start an agent")
    print("   agent-cli.py stop <agent>    — Stop an agent")
    print("   agent-cli.py logs <agent>    — View logs")
    print("   agent-cli.py deploy          — Deploy to production")
    
    return 0


def cmd_logs(args) -> int:
    """Show logs for an agent."""
    log_file = get_log_file(args.agent)
    
    if not log_file.exists():
        print(f"No logs found for {args.agent}")
        return 1
    
    lines = log_file.read_text().splitlines()
    if args.lines:
        lines = lines[-args.lines:]
    
    for line in lines:
        print(line)
    
    return 0


def cmd_deploy(args) -> int:
    """Deploy agent(s) to production with systemd service."""
    templates = load_templates()
    
    if args.agent == "all":
        agents = list(templates.keys())
    else:
        agents = [args.agent]
    
    hermes_bin = find_hermes_binary()
    if not hermes_bin:
        print("❌ Hermes not found.")
        return 1
    
    deployed = []
    for agent_name in agents:
        config = get_agent_config(agent_name)
        if not config:
            print(f"⚠️  {agent_name}: no config. Run setup-wizard first.")
            continue
        
        # Generate systemd service file
        service_content = f"""[Unit]
Description=Agent CLI - {agent_name}
After=network.target

[Service]
Type=simple
User={os.environ.get('USER', 'root')}
WorkingDirectory={Path.home() / '.hermes' / 'agent-cli'}
ExecStart={hermes_bin} gateway run --profile {agent_name}
Restart=always
RestartSec=10
StandardOutput=append:{LOG_DIR / f'{agent_name}.log'}
StandardError=append:{LOG_DIR / f'{agent_name}.log'}

[Install]
WantedBy=multi-user.target
"""
        
        service_name = f"agent-cli-{agent_name}"
        service_path = Path(f"/etc/systemd/system/{service_name}.service")
        
        # Try to install systemd service (requires root)
        if os.access(service_path.parent, os.W_OK):
            service_path.write_text(service_content)
            os.system(f"systemctl daemon-reload")
            os.system(f"systemctl enable {service_name}")
            os.system(f"systemctl start {service_name}")
            print(f"✅ {agent_name}: deployed as systemd service")
            deployed.append(agent_name)
        else:
            # Fallback: just show what would be created
            print(f"📄 {agent_name}: systemd service (needs sudo)")
            print(f"   Service file would be at: {service_path}")
            print(f"   To install manually:")
            print(f"   sudo cp agent-cli-{agent_name}.service /etc/systemd/system/")
            print(f"   sudo systemctl enable --now agent-cli-{agent_name}")
            
            # Save service file locally for user to install
            local_service = CONFIG_DIR / f"{agent_name}.service"
            local_service.write_text(service_content)
            print(f"   Service file saved: {local_service}")
            deployed.append(agent_name)
    
    print(f"\n📊 Deployed: {len(deployed)} services")
    return 0


def cmd_monitor(args) -> int:
    """Monitor agents and auto-restart on failure."""
    templates = load_templates()
    check_interval = args.interval or 30
    auto_restart = not args.no_restart
    max_retries = args.max_retries or 3
    
    # Track restart counts per agent: {agent_name: count}
    restart_counts = {}
    
    print(f"🔄 Starting monitor (interval: {check_interval}s, auto-restart: {auto_restart}, max_retries: {max_retries})")
    print("   Press Ctrl+C to stop\n")
    
    try:
        while True:
            for agent_name in templates.keys():
                config = get_agent_config(agent_name)
                if not config:
                    continue
                
                if is_running(agent_name):
                    # Reset count on successful run
                    if agent_name in restart_counts:
                        restart_counts[agent_name] = 0
                    continue
                
                # Agent crashed - check retry count
                current_retries = restart_counts.get(agent_name, 0)
                
                if auto_restart:
                    if current_retries < max_retries:
                        print(f"⚠️  {agent_name}: crashed, restarting ({current_retries + 1}/{max_retries})...")
                        hermes_bin = find_hermes_binary()
                        if hermes_bin:
                            cmd = build_hermes_command(agent_name, config)
                            log_file = get_log_file(agent_name)
                            try:
                                proc = subprocess.Popen(
                                    cmd,
                                    stdout=open(log_file, "a"),
                                    stderr=subprocess.STDOUT,
                                    start_new_session=True
                                )
                                pid_file = get_pid_file(agent_name)
                                pid_file.write_text(str(proc.pid))
                                start_time_file = CONFIG_DIR / f"{agent_name}.start_time"
                                start_time_file.write_text(str(time.time()))
                                restart_counts[agent_name] = current_retries + 1
                                print(f"   ✅ restarted (PID {proc.pid})")
                            except Exception as e:
                                print(f"   ❌ restart failed: {e}")
                    else:
                        print(f"🚨 {agent_name}: max retries ({max_retries}) exceeded, giving up")
                        print(f"   Run 'agent-cli start {agent_name}' to manually restart")
                else:
                    print(f"⚠️  {agent_name}: not running (auto-restart disabled)")
            
            time.sleep(check_interval)
    except KeyboardInterrupt:
        print("\n🛑 Monitor stopped")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="agent-cli",
        description="Agent CLI — Manage AI agent workflows"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # start command
    start_parser = subparsers.add_parser("start", help="Start an agent")
    start_parser.add_argument(
        "agent",
        nargs="?",
        default="all",
        help="Agent name or 'all' (default: all)"
    )
    start_parser.set_defaults(func=cmd_start)
    
    # stop command
    stop_parser = subparsers.add_parser("stop", help="Stop an agent")
    stop_parser.add_argument(
        "agent",
        nargs="?",
        default="all",
        help="Agent name or 'all' (default: all)"
    )
    stop_parser.set_defaults(func=cmd_stop)
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show status dashboard")
    status_parser.set_defaults(func=cmd_status)
    
    # logs command
    logs_parser = subparsers.add_parser("logs", help="View agent logs")
    logs_parser.add_argument("agent", help="Agent name")
    logs_parser.add_argument("-n", "--lines", type=int, default=None, help="Number of lines")
    logs_parser.set_defaults(func=cmd_logs)
    
    # deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy to production")
    deploy_parser.add_argument(
        "agent",
        nargs="?",
        default="all",
        help="Agent name or 'all' (default: all)"
    )
    deploy_parser.set_defaults(func=cmd_deploy)
    
    # monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor agents and auto-restart")
    monitor_parser.add_argument(
        "-i", "--interval",
        type=int,
        default=30,
        help="Check interval in seconds (default: 30)"
    )
    monitor_parser.add_argument(
        "--no-restart",
        action="store_true",
        help="Disable auto-restart on crash"
    )
    monitor_parser.add_argument(
        "-r", "--max-retries",
        type=int,
        default=3,
        help="Max restart attempts before giving up (default: 3)"
    )
    monitor_parser.set_defaults(func=cmd_monitor)
    
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())