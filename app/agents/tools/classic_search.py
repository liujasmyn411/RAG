from app.agents.tools.registry import registry
from app.services.knowledge_base import search_classic


@registry.register(
    name="search_classic_literature",
    description="在四大名著知识库中检索与用户问题相关的原文段落。适用于回答三国演义、水浒传、西游记、红楼梦相关的问题。",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "用户的查询内容，如'孙悟空大闹天宫'、'林黛玉葬花'"
            },
            "book_name": {
                "type": "string",
                "description": "限定书名，可选值：三国演义、水浒传、西游记、红楼梦。如不确定可省略。"
            },
            "top_k": {
                "type": "integer",
                "description": "返回的检索条数，默认 5 条",
                "default": 5,
            },
        },
        "required": ["query"],
    },
)
def classic_search_tool(query: str, book_name: str = None, top_k: int = 5):
    """四大名著语义检索工具"""
    results = search_classic(query=query, book_name=book_name, top_k=top_k)
    if not results:
        return "未检索到相关内容，许是知识库里没记着这一段。"

    # 格式化为 Agent 易读的文本
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] 《{r['book']}》{r['title']}（相似度{r['score']:.3f}）")
        content = r["content"].replace("\n", " ")
        lines.append(f"    {content[:300]}...")
    return "\n".join(lines)
