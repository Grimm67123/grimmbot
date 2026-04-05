import sys

with open('e:/GrimmBot/agent.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

config_end = 0
tools_start = 0
tools_end = 0
prompts_start = 0
prompts_end = 0

for i, line in enumerate(lines):
    if line.startswith('class Tools:'):
        tools_start = i
    if line.startswith('TOOL_DEFINITIONS = ['):
        prompts_start = i - 2
    if line.startswith('# ── Task Result & Logger'):
        prompts_end = i
    if line.startswith('# ── Custom Tool Registry'):
        config_end = i

# Write tools.py 
tools_lines = lines[tools_start:prompts_start]
with open('e:/GrimmBot/tools.py', 'w', encoding='utf-8') as f:
    f.write('"""\nGrimmBot — Built-in Tools Module\n"""\n\n')
    f.write('import os\nimport time\nimport json\nimport shutil\nimport difflib\nimport subprocess\nimport hashlib\nimport re\n')
    f.write('from datetime import datetime\nfrom pathlib import Path\n')
    f.write('from typing import Optional\n\n')
    f.write('from config import AgentConfig, is_path_safe, is_domain_allowed, is_command_allowed\n')
    f.write('from memory import get_memory\n')
    f.write('from screen import *\n\n')
    f.writelines(tools_lines)

# Write rewritten agent.py
agent_lines = lines[:config_end] + lines[prompts_end:]
# We need to inject the imports
imports = """
from config import AgentConfig, init_safe_paths, is_domain_allowed
from custom_tools import CustomToolRegistry
from prompts import TOOL_DEFINITIONS, SYSTEM_PROMPT_VISION, SYSTEM_PROMPT_TEXT
from tools import Tools
"""
new_agent = ''.join(agent_lines).replace('logger = logging.getLogger("agent")', 'logger = logging.getLogger("agent")\n' + imports)

with open('e:/GrimmBot/agent.py', 'w', encoding='utf-8') as f:
    f.write(new_agent)

print("Split completed.")
