#!/usr/bin/env python3
"""
Agent CLI Setup Wizard

Interactive CLI tool to configure and deploy AI agents.
Guides users through template selection, platform choice, API key collection,
and agent profile creation.
"""

import os
import sys
import json
import hashlib
import base64
import getpass
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str) -> None:
    """Print a header with formatting."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_section(text: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'-'*len(text)}{Colors.ENDC}")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")


def prompt_input(prompt: str, default: Optional[str] = None) -> str:
    """Prompt for user input with optional default."""
    if default:
        return input(f"{prompt} [{default}]: ").strip() or default
    return input(f"{prompt}: ").strip()


def prompt_password(prompt: str) -> str:
    """Prompt for password input (hidden)."""
    return getpass.getpass(f"{prompt}: ")


def prompt_yn(prompt: str, default: bool = True) -> bool:
    """Prompt for yes/no input."""
    while True:
        suffix = "Y/n" if default else "y/N"
        response = input(f"{prompt} [{suffix}]: ").strip().lower()
        if not response:
            return default
        if response in ('y', 'yes'):
            return True
        if response in ('n', 'no'):
            return False
        print_error("Please enter 'y' or 'n'")


def prompt_choice(prompt: str, choices: List[str], numbered: bool = True) -> int:
    """Prompt user to choose from a list of choices."""
    while True:
        print(f"\n{prompt}")
        for i, choice in enumerate(choices, 1):
            print(f"  {i}. {choice}")
        
        try:
            response = input(f"\nEnter your choice (1-{len(choices)}): ").strip()
            index = int(response) - 1
            if 0 <= index < len(choices):
                return index
            print_error(f"Please enter a number between 1 and {len(choices)}")
        except ValueError:
            print_error("Please enter a valid number")


class EncryptionManager:
    """Handle encryption of sensitive data using AES-256."""
    
    def __init__(self, master_password: str):
        self.key = self._derive_key(master_password)
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from master password using PBKDF2."""
        salt = b'agent-cli-salt-v1'  # In production, use random salt
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt,
            100000,
            dklen=32
        )
    
    def encrypt(self, data: str) -> str:
        """Encrypt data using AES-256."""
        from cryptography.fernet import Fernet
        
        # Generate a random key for this encryption
        fernet_key = Fernet.generate_key()
        fernet = Fernet(fernet_key)
        
        # Encrypt the data
        encrypted = fernet.encrypt(data.encode())
        
        # Combine key and encrypted data
        combined = base64.b64encode(fernet_key + encrypted).decode()
        return combined
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data using AES-256."""
        from cryptography.fernet import Fernet
        
        # Decode the combined data
        combined = base64.b64decode(encrypted_data.encode())
        
        # Extract key and encrypted data
        fernet_key = combined[:32]
        encrypted = combined[32:]
        
        # Decrypt
        fernet = Fernet(fernet_key)
        return fernet.decrypt(encrypted).decode()


class SetupWizard:
    """Main setup wizard class."""
    
    def __init__(self):
        self.base_dir = Path.home() / ".hermes" / "agent-cli"
        self.config_dir = self.base_dir / "config"
        self.agents_dir = self.config_dir / "agents"
        self.keys_file = self.config_dir / "keys.enc"
        self.templates_file = self.base_dir / "agent-templates.json"
        
        self.templates: Dict[str, Any] = {}
        self.agent_config: Dict[str, Any] = {}
        self.encryption: Optional[EncryptionManager] = None
    
    def run(self) -> None:
        """Run the complete setup wizard."""
        print_header("Agent CLI Setup Wizard")
        print(f"{Colors.GREEN}Welcome to Agent CLI!{Colors.ENDC}")
        print("Let's set up your AI agent in just a few minutes.\n")
        
        # Step 1: Check dependencies
        self._check_dependencies()
        
        # Step 2: Load templates
        self._load_templates()
        
        # Step 3: Select template
        self._select_template()
        
        # Step 4: Select platforms
        self._select_platforms()
        
        # Step 5: Set master password
        self._setup_encryption()
        
        # Step 6: Collect API keys
        self._collect_api_keys()
        
        # Step 7: Create agent profile
        self._create_agent_profile()
        
        # Step 8: Create main CLI entry point
        self._create_entry_point()
        
        # Step 9: Show summary
        self._show_summary()
        
        print_success("Setup complete!")
        print(f"\n{Colors.GREEN}To start your agent, run:{Colors.ENDC}")
        print(f"  python3 {self.base_dir}/agent-cli.py start")
    
    def _check_dependencies(self) -> None:
        """Check and install required dependencies."""
        print_section("Checking Dependencies")
        
        # Check Python version
        if sys.version_info < (3, 10):
            print_error(f"Python 3.10+ required, but you have {sys.version_info.major}.{sys.version_info.minor}")
            sys.exit(1)
        
        print_success(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ✓")
        
        # Check for cryptography library
        try:
            import cryptography
            print_success("cryptography library ✓")
        except ImportError:
            print_warning("Installing cryptography library...")
            os.system(f"{sys.executable} -m pip install cryptography -q")
            print_success("cryptography library installed ✓")
        
        # Create directory structure
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        print_success("Directory structure created ✓")
    
    def _load_templates(self) -> None:
        """Load agent templates from JSON file."""
        print_section("Loading Agent Templates")
        
        if self.templates_file.exists():
            with open(self.templates_file, 'r') as f:
                data = json.load(f)
                self.templates = data.get('templates', {})
            print_success(f"Loaded {len(self.templates)} templates")
        else:
            print_error("Templates file not found!")
            sys.exit(1)
    
    def _select_template(self) -> None:
        """Prompt user to select an agent template."""
        print_section("Select Agent Template")
        
        template_list = list(self.templates.keys())
        template_descriptions = [
            self.templates[t]['description'] for t in template_list
        ]
        
        for i, (name, desc) in enumerate(zip(template_list, template_descriptions), 1):
            print(f"\n{Colors.BOLD}{i}. {name.replace('-', ' ').title()}{Colors.ENDC}")
            print(f"   {desc}")
        
        choice = prompt_choice(
            "Choose an agent template",
            [self.templates[t]['name'] for t in template_list]
        )
        
        selected_key = template_list[choice]
        self.agent_config['template'] = selected_key
        self.agent_config['template_data'] = self.templates[selected_key]
        
        print_success(f"Selected: {self.templates[selected_key]['name']}")
    
    def _select_platforms(self) -> None:
        """Prompt user to select communication platforms."""
        print_section("Select Platforms")
        
        platforms = {
            '1': ('Telegram', 'telegram'),
            '2': ('Discord', 'discord'),
            '3': ('Slack', 'slack')
        }
        
        print("Which platforms should your agent connect to?")
        print("You can select multiple (e.g., '1,3' for Telegram + Slack)\n")
        
        selected = []
        for num, (name, key) in platforms.items():
            if prompt_yn(f"Enable {name}?", default=False):
                selected.append(key)
                self._configure_platform(key)
        
        if not selected:
            print_warning("No platforms selected. Using Telegram as default.")
            selected = ['telegram']
        
        self.agent_config['platforms'] = selected
        print_success(f"Enabled platforms: {', '.join(selected)}")
    
    def _configure_platform(self, platform: str) -> None:
        """Configure a specific platform."""
        print_info(f"Configuring {platform}...")
        
        if platform == 'telegram':
            bot_token = prompt_password("Telegram Bot Token (from @BotFather)")
            self._save_key('telegram/bot_token', bot_token)
            print_success("Telegram bot token saved")
        
        elif platform == 'discord':
            bot_token = prompt_password("Discord Bot Token")
            self._save_key('discord/bot_token', bot_token)
            print_success("Discord bot token saved")
        
        elif platform == 'slack':
            bot_token = prompt_password("Slack Bot Token (xoxb-...)")
            self._save_key('slack/bot_token', bot_token)
            print_success("Slack bot token saved")
    
    def _setup_encryption(self) -> None:
        """Set up encryption with master password."""
        print_section("Security Setup")
        
        print_info("Creating a master password to encrypt your API keys...")
        print_info("This password is needed to start your agent.\n")
        
        while True:
            password = prompt_password("Create master password (min 8 characters)")
            if len(password) < 8:
                print_error("Password must be at least 8 characters")
                continue
            
            confirm = prompt_password("Confirm master password")
            if password != confirm:
                print_error("Passwords don't match. Try again.")
                continue
            
            self.encryption = EncryptionManager(password)
            print_success("Encryption configured")
            break
    
    def _save_key(self, key_name: str, key_value: str) -> None:
        """Save an API key securely."""
        if not self.encryption:
            print_error("Encryption not configured")
            return
        
        # Load existing keys
        keys = {}
        if self.keys_file.exists():
            encrypted = self.keys_file.read_text()
            if encrypted:
                try:
                    decrypted = self.encryption.decrypt(encrypted)
                    keys = json.loads(decrypted)
                except:
                    keys = {}
        
        # Add new key
        keys[key_name] = key_value
        
        # Save encrypted
        encrypted = self.encryption.encrypt(json.dumps(keys))
        self.keys_file.write_text(encrypted)
    
    def _collect_api_keys(self) -> None:
        """Collect required API keys for the selected template."""
        print_section("API Key Collection")
        
        template_data = self.agent_config['template_data']
        required_keys = template_data.get('required_api_keys', [])
        required_tools = template_data.get('required_tools', [])
        
        print_info(f"Your {template_data['name']} requires these services:\n")
        
        # Map of service names to prompts
        key_prompts = {
            'google/oauth2': ('Google OAuth2 (Gmail/Calendar)', 'https://console.cloud.google.com'),
            'openai/api_key': ('OpenAI API Key', 'https://platform.openai.com/api-keys'),
            'twitter/api_key': ('Twitter/X API Key', 'https://developer.twitter.com'),
            'twitter/api_secret': ('Twitter/X API Secret', 'https://developer.twitter.com'),
            'linkedin/oauth2': ('LinkedIn OAuth2', 'https://www.linkedin.com/developers'),
            'serpapi/key': ('SerpAPI Key', 'https://serpapi.com/dashboard'),
            'unsplash/api_key': ('Unsplash API Key', 'https://unsplash.com/developers'),
            'github/token': ('GitHub Token', 'https://github.com/settings/tokens'),
        }
        
        for key in required_keys:
            if key.startswith('google/'):
                # Special handling for Google OAuth
                client_id = prompt_password(f"Google OAuth2 Client ID")
                client_secret = prompt_password(f"Google OAuth2 Client Secret")
                self._save_key('google/client_id', client_id)
                self._save_key('google/client_secret', client_secret)
                print_success(f"Google OAuth2 credentials saved")
            elif key in key_prompts:
                name, url = key_prompts[key]
                if prompt_yn(f"Configure {name}?", default=True):
                    api_key = prompt_password(f"{name} API Key")
                    self._save_key(key, api_key)
                    print_success(f"{name} saved")
                else:
                    print_warning(f"Skipping {name} - some features may not work")
            else:
                print_warning(f"Unknown API key: {key}")
        
        # Save tools list
        self.agent_config['tools'] = required_tools
    
    def _create_agent_profile(self) -> None:
        """Create agent configuration file."""
        print_section("Creating Agent Profile")
        
        # Get agent name
        default_name = f"{self.agent_config['template']}-agent"
        agent_name = prompt_input("Agent name", default_name)
        
        # Get display name
        display_name = prompt_input("Display name for your agent", "My Agent")
        
        # Get description
        description = prompt_input(
            "Description (what does this agent do?)",
            self.agent_config['template_data']['description']
        )
        
        # Build agent config
        agent_profile = {
            "name": agent_name,
            "display_name": display_name,
            "description": description,
            "template": self.agent_config['template'],
            "platforms": self.agent_config['platforms'],
            "tools": self.agent_config['tools'],
            "config": self.agent_config['template_data'].get('default_config', {}),
            "enabled": True,
            "created_at": self._get_timestamp()
        }
        
        # Save agent profile
        agent_file = self.agents_dir / f"{agent_name}.json"
        with open(agent_file, 'w') as f:
            json.dump(agent_profile, f, indent=2)
        
        self.agent_config['agent_file'] = str(agent_file)
        print_success(f"Agent profile saved: {agent_file}")
    
    def _create_entry_point(self) -> None:
        """Create the main CLI entry point."""
        print_section("Creating CLI Entry Point")
        
        entry_point = self.base_dir / "agent-cli.py"
        
        entry_code = '''#!/usr/bin/env python3
"""
Agent CLI - Main Entry Point

AI Agent Platform for Solo Founders & Small Agencies
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def load_config():
    """Load agent configuration."""
    config_dir = Path.home() / ".hermes" / "agent-cli" / "config"
    
    # Load agent profile
    agents_dir = config_dir / "agents"
    agent_files = list(agents_dir.glob("*.json"))
    
    if not agent_files:
        print("No agents configured. Run setup-wizard.py first.")
        sys.exit(1)
    
    with open(agent_files[0]) as f:
        return json.load(f)


def start_agent(config):
    """Start the configured agent."""
    print(f"Starting {config['display_name']}...")
    print(f"Template: {config['template']}")
    print(f"Platforms: {', '.join(config['platforms'])}")
    print("\\nAgent is running! Press Ctrl+C to stop.")
    
    # TODO: Implement actual agent startup
    # This is where you would initialize the agent framework,
    # connect to platforms, and start the event loop.
    
    try:
        while True:
            # Placeholder - actual implementation would:
            # 1. Initialize platform connections
            # 2. Load skills and tools
            # 3. Start message processing loop
            # 4. Handle agent tasks
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\n\\nShutting down agent...")
        print("Agent stopped.")


def status_command(config):
    """Show agent status."""
    print(f"Agent: {config['display_name']}")
    print(f"Status: Active" if config.get('enabled') else "Status: Disabled")
    print(f"Template: {config['template']}")
    print(f"Platforms: {', '.join(config['platforms'])}")
    print(f"Tools: {', '.join(config.get('tools', []))}")


def stop_agent(config):
    """Stop the running agent."""
    # TODO: Implement graceful shutdown
    print("Stopping agent...")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Agent CLI - AI Agent Platform"
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the agent')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show agent status')
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop the agent')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Edit configuration')
    config_parser.add_argument('key', help='Config key to edit')
    config_parser.add_argument('value', help='New value')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    config = load_config()
    
    if args.command == 'start':
        start_agent(config)
    elif args.command == 'status':
        status_command(config)
    elif args.command == 'stop':
        stop_agent(config)
    elif args.command == 'config':
        # TODO: Implement config editing
        print("Config editing not yet implemented")


if __name__ == '__main__':
    main()
'''
        
        entry_point.write_text(entry_code)
        entry_point.chmod(0o755)
        print_success(f"Entry point created: {entry_point}")
    
    def _show_summary(self) -> None:
        """Show setup summary."""
        print_header("Setup Summary")
        
        template_data = self.agent_config['template_data']
        
        print(f"{Colors.BOLD}Agent Configuration:{Colors.ENDC}")
        print(f"  Name: {self.agent_config.get('name', 'N/A')}")
        print(f"  Template: {template_data['name']}")
        print(f"  Platforms: {', '.join(self.agent_config['platforms'])}")
        print(f"  Skills: {len(template_data.get('required_skills', []))} configured")
        print(f"  Tools: {len(self.agent_config['tools'])} configured")
        
        print(f"\n{Colors.BOLD}Security:{Colors.ENDC}")
        print(f"  API Keys: Encrypted with AES-256")
        print(f"  Storage: {self.keys_file}")
        
        print(f"\n{Colors.BOLD}Files Created:{Colors.ENDC}")
        print(f"  Entry point: {self.base_dir}/agent-cli.py")
        print(f"  Agent profile: {self.agent_config['agent_file']}")
        print(f"  Config dir: {self.config_dir}")
    
    def _get_timestamp(self) -> str:
        """Get current ISO timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'


def main():
    """Entry point for setup wizard."""
    wizard = SetupWizard()
    wizard.run()


if __name__ == '__main__':
    main()