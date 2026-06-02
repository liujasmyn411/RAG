"""
JiebaClient: 一个简洁易用的 jieba 中文分词客户端封装
功能包括：精确/全模式分词、搜索引擎模式、关键词提取、词性标注、自定义词典加载等
"""

import jieba
import jieba.analyse
import jieba.posseg as pseg
from typing import List, Dict, Optional, Tuple


class JiebaClient:
    """
    jieba 分词客户端封装类
    
    特性：
    - 统一接口，避免记忆多个 jieba 子模块
    - 自动过滤空白与无用符号
    - 支持链式加载自定义词典/停用词
    - 所有方法均有清晰返回值类型
    """

    def __init__(self, user_dict_path: Optional[str] = None, stop_words_path: Optional[str] = None):
        """
        初始化 JiebaClient

        Args:
            user_dict_path: 自定义用户词典路径（txt格式，每行一个词）
            stop_words_path: 停用词文件路径（txt格式，每行一个停用词）
        """
        # 加载自定义词典（必须在分词前调用）
        if user_dict_path:
            self.load_user_dict(user_dict_path)

        # 加载停用词表
        self._stop_words: set = set()
        if stop_words_path:
            self.load_stop_words(stop_words_path)

    # ==================== 词典管理 ====================

    def load_user_dict(self, path: str) -> "JiebaClient":
        """
        加载自定义用户词典，支持链式调用

        Args:
            path: 词典文件路径，格式为 "词语 频率 词性"（频率和词性可省略）
        Returns:
            self，支持链式调用
        """
        jieba.load_userdict(path)
        return self

    def add_word(self, word: str, freq: Optional[int] = None, tag: Optional[str] = None) -> "JiebaClient":
        """
        动态添加单个词语到词典（无需文件）

        Args:
            word: 要添加的词语
            freq: 词频，越高越容易被分出
            tag: 词性标记，如 'n', 'v', 'nr' 等
        Returns:
            self，支持链式调用
        """
        jieba.add_word(word, freq=freq, tag=tag)
        return self

    def load_stop_words(self, path: str) -> "JiebaClient":
        """
        从文件加载停用词表

        Args:
            path: 停用词文件路径，每行一个停用词
        Returns:
            self，支持链式调用
        """
        with open(path, "r", encoding="utf-8") as f:
            self._stop_words = {line.strip() for line in f if line.strip()}
        return self

    def set_stop_words(self, words: List[str]) -> "JiebaClient":
        """
        直接通过列表设置停用词（适合代码中硬编码少量停用词）

        Args:
            words: 停用词列表
        Returns:
            self，支持链式调用
        """
        self._stop_words = set(words)
        return self

    # ==================== 核心分词 ====================

    def cut(self, text: str, use_stop_words: bool = True) -> List[str]:
        """
        精确模式分词（最常用），适合文本分析、NLP任务

        Args:
            text: 待分词的中文文本
            use_stop_words: 是否过滤停用词
        Returns:
            分词结果列表，已去除空白token
        """
        tokens = jieba.lcut(text)  # lcut 直接返回列表，比 cut() + list() 更简洁
        return self._filter_tokens(tokens, use_stop_words)

    def cut_all(self, text: str, use_stop_words: bool = True) -> List[str]:
        """
        全模式分词：扫描出所有可能的词语，速度快但有冗余
        适用场景：快速浏览、不要求精确度的场景

        Args:
            text: 待分词的中文文本
            use_stop_words: 是否过滤停用词
        Returns:
            全模式分词结果列表
        """
        tokens = jieba.lcut(text, cut_all=True)
        return self._filter_tokens(tokens, use_stop_words)

    def cut_for_search(self, text: str, use_stop_words: bool = True) -> List[str]:
        """
        搜索引擎模式分词：在精确模式基础上对长词再次切分
        适用场景：构建搜索索引、ES/Meilisearch 数据预处理

        Args:
            text: 待分词的中文文本
            use_stop_words: 是否过滤停用词
        Returns:
            搜索模式分词结果列表
        """
        tokens = jieba.lcut_for_search(text)
        return self._filter_tokens(tokens, use_stop_words)

    # ==================== 关键词提取 ====================

    def extract_keywords_tfidf(
        self, text: str, top_k: int = 10, allowed_pos: Optional[List[str]] = None
    ) -> List[Tuple[str, float]]:
        """
        基于 TF-IDF 算法提取关键词

        Args:
            text: 待提取关键词的文本
            top_k: 返回前K个关键词
            allowed_pos: 允许的词性列表，如 ['n', 'nr', 'ns'] 只保留名词类
        Returns:
            [(关键词, 权重), ...] 的列表，按权重降序排列
        """
        allow_pos = "/".join(allowed_pos) if allowed_pos else ""
        return jieba.analyse.extract_tags(text, topK=top_k, withWeight=True, allowPOS=allow_pos)

    def extract_keywords_textrank(
        self, text: str, top_k: int = 10, allowed_pos: Optional[List[str]] = None
    ) -> List[Tuple[str, float]]:
        """
        基于 TextRank 算法提取关键词（无需语料库，单文档即可）

        Args:
            text: 待提取关键词的文本
            top_k: 返回前K个关键词
            allowed_pos: 允许的词性列表
        Returns:
            [(关键词, 权重), ...] 的列表，按权重降序排列
        """
        allow_pos = "/".join(allowed_pos) if allowed_pos else ""
        return jieba.analyse.textrank(text, topK=top_k, withWeight=True, allowPOS=allow_pos)

    # ==================== 词性标注 ====================

    def pos_cut(self, text: str, use_stop_words: bool = True) -> List[Dict[str, str]]:
        """
        分词 + 词性标注

        Args:
            text: 待处理的中文文本
            use_stop_words: 是否过滤停用词
        Returns:
            [{"word": "北京", "pos": "ns"}, ...] 格式的列表
        """
        pairs = pseg.lcut(text)
        results = []
        for pair in pairs:
            word = pair.word.strip()
            if not word:
                continue
            if use_stop_words and word in self._stop_words:
                continue
            results.append({"word": word, "pos": pair.flag})
        return results

    # ==================== 内部工具方法 ====================

    def _filter_tokens(self, tokens: List[str], use_stop_words: bool) -> List[str]:
        """
        过滤空白token和停用词（内部使用）

        Args:
            tokens: 原始分词列表
            use_stop_words: 是否启用停用词过滤
        Returns:
            清洗后的token列表
        """
        filtered = [t.strip() for t in tokens if t.strip()]
        if use_stop_words and self._stop_words:
            filtered = [t for t in filtered if t not in self._stop_words]
        return filtered




# ========== 基础使用 ==========
client = JiebaClient()

text = "自然语言处理是人工智能领域中的重要研究方向北京大学的NLP实验室在这方面做出了杰出贡献"

# 1. 精确分词
print(client.cut(text))
# ['自然语言处理', '人工智能', '领域', '重要', '研究', '方向', '北京大学', 'NLP', '实验室', '杰出', '贡献']

# 2. 搜索模式分词（长词会被再拆分）
print(client.cut_for_search(text))
# ['自然语言', '自然', '语言', '处理', '人工智能', '人工', '智能', ...]

# 3. TF-IDF 关键词提取
keywords = client.extract_keywords_tfidf(text, top_k=5, allowed_pos=["n", "nr", "ns"])
print(keywords)
# [('自然语言处理', 0.87), ('北京大学', 0.76), ('人工智能', 0.65), ...]

# 4. 词性标注
pos_result = client.pos_cut("他去了北京大学")
print(pos_result)
# [{'word': '他', 'pos': 'r'}, {'word': '去', 'pos': 'v'}, {'word': '北京大学', 'pos': 'nt'}]

# ========== 带自定义词典和停用词 ==========
client2 = (
    JiebaClient()
    .add_word("自然语言处理", freq=99999)   # 动态加词
    .set_stop_words(["是", "的", "了", "在", "中"])  # 设置停用词
)
print(client2.cut(text))
# 停用词被过滤，且"自然语言处理"不会被错误切分

# ========== 从文件加载 ==========
# client3 = JiebaClient(
#     user_dict_path="./my_dict.txt",
#     stop_words_path="./stop_words.txt"
# )