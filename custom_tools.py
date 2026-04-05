"""
GrimmBot — Custom Tool Registry Module
"""

import re
import json
import logging
from pathlib import Path
from typing import Callable

logger = logging.getLogger("agent")

class CustomToolRegistry:
    """Manages dynamically created tools persisted to a single JSON ledger."""

    def __init__(self, tools_dir: str):
        self.tools_dir = Path(tools_dir)
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        # Unified ledger file
        self.tools_file = self.tools_dir / "custom_tools.json"
        
        self._functions: dict[str, Callable] = {}
        self._definitions: list[dict] = []
        self._requires_approval: dict[str, bool] = {}
        
        self._load_all()

    def _load_all(self):
        if not self.tools_file.exists():
            return
        try:
            stored_tools = json.loads(self.tools_file.read_text())
            for info in stored_tools:
                # Execute and map the stored python string natively
                self._load_tool(info["name"], info.get("code", ""), info)
        except Exception as e:
            logger.error("Failed to load unified custom tools: %s", e)

    def _load_tool(self, name: str, code: str, info: dict):
        try:
            namespace = {"__builtins__": __builtins__}
            # Compile and execute the raw python code into the local namespace
            exec(compile(code, f"<tool_{name}>", "exec"), namespace)
            if name in namespace and callable(namespace[name]):
                self._functions[name] = namespace[name]
                self._requires_approval[name] = info.get("requires_approval", True)
                self._definitions.append({
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": info.get("description", f"Custom tool: {name}"),
                        "parameters": info.get("parameters", {"type": "object", "properties": {}}),
                    },
                })
        except Exception as e:
            logger.error("Failed to compile tool %s: %s", name, e)

    def create_tool(self, name: str, description: str, parameters: dict, code: str, requires_approval: bool = True) -> str:
        if not re.match(r"^[a-z_][a-z0-9_]{0,49}$", name):
            return "Invalid name. Use lowercase, numbers, underscores. Max 50 chars."

        # Fetch the current state of the JSON ledger
        manifest = []
        if self.tools_file.exists():
            try:
                manifest = json.loads(self.tools_file.read_text())
            except Exception:
                pass
                
        # Purge any existing iteration of this tool to prevent duplicates
        manifest = [t for t in manifest if t["name"] != name]
        
        # Append the new tool metadata alongside the raw python string
        manifest.append({
            "name": name, 
            "description": description, 
            "parameters": parameters, 
            "code": code, 
            "requires_approval": requires_approval
        })
        
        # Commit the entire array back to the JSON file
        self.tools_file.write_text(json.dumps(manifest, indent=2))

        # Clear old mappings in active memory
        self._functions.pop(name, None)
        self._requires_approval.pop(name, None)
        self._definitions = [d for d in self._definitions if d["function"]["name"] != name]
        
        # Load the newly injected code into the active execution pipeline
        self._load_tool(name, code, {
            "name": name, 
            "description": description, 
            "parameters": parameters, 
            "requires_approval": requires_approval
        })

        return f"Custom tool '{name}' created and successfully saved to custom_tools.json" if name in self._functions else f"Tool '{name}' saved but failed to load due to python syntax error"

    def set_approval_requirement(self, name: str, requires_approval: bool):
        """Dynamically updates the approval state of a tool in memory and on disk."""
        if name not in self._functions:
            return
        
        # Update active memory
        self._requires_approval[name] = requires_approval
        
        # Rewrite the ledger to make the preference permanent
        if self.tools_file.exists():
            try:
                manifest = json.loads(self.tools_file.read_text())
                for t in manifest:
                    if t["name"] == name:
                        t["requires_approval"] = requires_approval
                self.tools_file.write_text(json.dumps(manifest, indent=2))
            except Exception as e:
                logger.error("Failed to update approval requirement for %s: %s", name, e)

    def list_tools(self) -> list[str]:
        return list(self._functions.keys())

    def get_definitions(self) -> list[dict]:
        return self._definitions.copy()

    def call(self, name: str, args: dict) -> str:
        func = self._functions.get(name)
        if not func:
            return f"Custom tool '{name}' not found"
        try:
            return str(func(**args))
        except Exception as e:
            return f"Custom tool runtime error: {e}"

    def delete_tool(self, name: str) -> str:
        # Purge from active memory
        self._functions.pop(name, None)
        self._requires_approval.pop(name, None)
        self._definitions = [d for d in self._definitions if d["function"]["name"] != name]
        
        # Rewrite the ledger excluding the target tool
        if self.tools_file.exists():
            try:
                manifest = [t for t in json.loads(self.tools_file.read_text()) if t["name"] != name]
                self.tools_file.write_text(json.dumps(manifest, indent=2))
            except Exception:
                pass
                
        return f"Custom tool '{name}' deleted from custom_tools.json"