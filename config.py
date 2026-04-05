"""
GrimmBot — Configuration and Safety Module
"""

import os
import re
import shlex
import logging
from pathlib import Path
from urllib.parse import urlparse
from dataclasses import dataclass, field

logger = logging.getLogger("agent")


# ── Configuration ─────────────────────────────────────────────────────────────


@dataclass
class AgentConfig:
    model: str = ""
    vision_model: str = ""
    use_vision: bool = True
    allowed_domains: list[str] = field(default_factory=list)
    allow_all_domains: bool = False
    allowed_commands: list[str] = field(default_factory=list)
    allow_all_commands: bool = False
    task_timeout: int = 300
    max_iterations: int = 50
    max_shell_output: int = 8000
    session_key: str = ""
    wormhole_dir: str = "wormhole"
    workspace_dir: str = "workspace"
    profile_dir: str = "data/profiles"
    custom_tools_dir: str = "data/custom_tools"
    adaptation_file: str = "data/adaptation.json"
    wormhole_max_file_size: int = 52428800
    wormhole_blocked_extensions: list[str] = field(default_factory=list)
    monitor_timeout: int = 3600

    @classmethod
    def from_env(cls) -> "AgentConfig":
        raw_domains = os.getenv("ALLOWED_DOMAINS", "")
        domains = [d.strip().lower() for d in raw_domains.split(",") if d.strip()]
        raw_cmds = os.getenv("ALLOWED_COMMANDS", "")
        cmds = [c.strip() for c in raw_cmds.split(",") if c.strip()]
        raw_blocked = os.getenv("WORMHOLE_BLOCKED_EXTENSIONS", "")
        blocked = [e.strip().lower() for e in raw_blocked.split(",") if e.strip()]
        model = os.getenv("LLM_MODEL", "").strip() or "gemini/gemini-1.5-flash"
        vision_model = os.getenv("VISION_MODEL", "").strip() or model
        use_vision = os.getenv("USE_VISION", "true").lower() == "true"
        return cls(
            model=model, vision_model=vision_model, use_vision=use_vision,
            allowed_domains=domains, allow_all_domains="*" in domains,
            allowed_commands=cmds, allow_all_commands="*" in cmds,
            task_timeout=int(os.getenv("TASK_TIMEOUT_SECONDS", "300")),
            max_iterations=int(os.getenv("MAX_ITERATIONS", "50")),
            max_shell_output=int(os.getenv("MAX_SHELL_OUTPUT_CHARS", "8000")),
            session_key=os.getenv("SESSION_ENCRYPTION_KEY", ""),
            wormhole_dir=os.getenv("WORMHOLE_DIR", "wormhole"),
            workspace_dir=os.getenv("WORKSPACE_DIR", "workspace"),
            profile_dir=os.getenv("PROFILE_DIR", "data/profiles"),
            custom_tools_dir=os.getenv("CUSTOM_TOOLS_DIR", "data/custom_tools"),
            adaptation_file=os.getenv("ADAPTATION_FILE", "data/adaptation.json"),
            wormhole_max_file_size=int(os.getenv("WORMHOLE_MAX_FILE_SIZE", "52428800")),
            wormhole_blocked_extensions=blocked,
            monitor_timeout=int(os.getenv("MONITOR_TIMEOUT_SECONDS", "3600")),
        )


# ── Safety ────────────────────────────────────────────────────────────────────

SAFE_PATHS: list[str] = []


def init_safe_paths(config: AgentConfig):
    global SAFE_PATHS
    SAFE_PATHS = [
        str(Path(config.wormhole_dir).resolve()),
        str(Path(config.workspace_dir).resolve()),
        str(Path(config.custom_tools_dir).resolve()),
    ]


def is_path_safe(path_str: str) -> bool:
    try:
        resolved = str(Path(path_str).resolve())
        return any(resolved.startswith(root) for root in SAFE_PATHS)
    except Exception:
        return False


def is_domain_allowed(url: str, config: AgentConfig) -> bool:
    if config.allow_all_domains:
        return True
    try:
        hostname = (urlparse(url).hostname or "").lower()
        if not hostname:
            return False
        return any(hostname == d or hostname.endswith(f".{d}") for d in config.allowed_domains)
    except Exception:
        return False


def is_command_allowed(cmd: str, config: AgentConfig) -> bool:
    if config.allow_all_commands:
        return True
    blocked_chars = [";", "&&", "||", "|", "`", "$(", "${", "\n", "\r"]
    if any(c in cmd for c in blocked_chars):
        return False
    try:
        parts = shlex.split(cmd)
        base_cmd = parts[0] if parts else ""
    except ValueError:
        base_cmd = cmd.split()[0] if cmd.split() else ""
    return base_cmd in config.allowed_commands
