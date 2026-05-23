from pathlib import Path
from jinja2 import Template
from app.agents.tools.registry import registry


def load_system_prompt() -> str:
    """加载并渲染林黛玉系统 Prompt"""
    prompt_path = Path("prompts/lin_daiyu_system.md")
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt 文件不存在: {prompt_path}")

    template = Template(prompt_path.read_text(encoding="utf-8"))
    tools_description = registry.describe_tools()
    return template.render(tools_description=tools_description)
