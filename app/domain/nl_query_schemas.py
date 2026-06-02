"""NL 查询请求/响应 Schema"""

from typing import Optional

from pydantic import BaseModel, Field


class NLQueryRequest(BaseModel):
    """自然语言查询请求"""
    question: str = Field(..., description="自然语言查询问题", min_length=1, max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {
                "question": "有哪些女生的数学成绩超过85分？"
            }
        }


class NLQueryResponse(BaseModel):
    """自然语言查询响应"""
    question: str = Field(..., description="原始问题")
    sql: Optional[str] = Field(None, description="生成的 SQL")
    sql_error: Optional[str] = Field(None, description="SQL 安全校验/执行错误")
    result: Optional[list] = Field(None, description="原始查询结果")
    result_row_count: int = Field(0, description="结果行数")
    answer: str = Field("", description="格式化后的自然语言回答")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "有哪些女生的数学成绩超过85分？",
                "sql": "SELECT s.name, sc.score FROM students s JOIN scores sc ...",
                "result": [{"name": "小红", "score": 92.0}],
                "result_row_count": 1,
                "answer": "数学成绩超过85分的女生有1人:\n| 姓名 | 分数 |\n|------|------|\n| 小红 | 92.0 |"
            }
        }
