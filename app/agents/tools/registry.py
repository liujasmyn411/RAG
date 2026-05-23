import inspect
import json
from typing import Callable, Dict, Any, List


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
    ):
        """装饰器：注册一个工具"""
        def decorator(func: Callable) -> Callable:
            self._tools[name] = {
                "name": name,
                "description": description,
                "parameters": parameters,
                "func": func,
            }
            return func
        return decorator

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """生成 OpenAI 格式的 tools 列表"""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in self._tools.values()
        ]

    async def execute(self, name: str, arguments: str) -> str:
        """执行工具，返回字符串结果"""
        if name not in self._tools:
            raise ValueError(f"未知工具: {name}")

        tool = self._tools[name]
        func = tool["func"]

        try:
            args_dict = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError:
            return f"参数解析失败: {arguments}"

        # 检查函数是否是 async
        if inspect.iscoroutinefunction(func):
            result = await func(**args_dict)
        else:
            result = func(**args_dict)

        # 统一转为字符串
        if isinstance(result, (list, dict)):
            return json.dumps(result, ensure_ascii=False, default=str)
        return str(result) if result is not None else ""

    def describe_tools(self) -> str:
        """生成供 Prompt 使用的工具描述文本"""
        lines = []
        for t in self._tools.values():
            lines.append(f"- {t['name']}: {t['description']}")
            lines.append(f"  参数: {json.dumps(t['parameters'], ensure_ascii=False)}")
        return "\n".join(lines)


# 全局注册表实例
registry = ToolRegistry()
