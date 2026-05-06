"""
NLP 语义理解模块
使用 sentence-transformers 进行文本语义相似度计算
"""
import numpy as np
from sentence_transformers import SentenceTransformer, util

# 加载中文语义模型（首次运行会自动下载，约 400MB）
# 模型会自动缓存到 ~/.cache/huggingface/hub
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'

class SemanticAnalyzer:
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载语义模型"""
        try:
            self.model = SentenceTransformer(MODEL_NAME)
            print(f"语义模型加载成功: {MODEL_NAME}")
        except Exception as e:
            print(f"模型加载失败: {e}")
            self.model = None
    
    def encode(self, text):
        """将文本转换为向量"""
        if self.model is None:
            return None
        # 限制文本长度，避免过长的文本影响性能
        if len(text) > 5000:
            text = text[:5000]
        return self.model.encode(text, convert_to_tensor=True)
    
    def similarity(self, text1, text2):
        """计算两个文本的语义相似度（0-1）"""
        if self.model is None:
            return 0.5
        vec1 = self.encode(text1)
        vec2 = self.encode(text2)
        if vec1 is None or vec2 is None:
            return 0.5
        return util.pytorch_cos_sim(vec1, vec2).item()
    
    def compare_with_dimension(self, text, dimension_description):
        """
        将方案文本与评价维度描述进行语义对比
        dimension_description: 该维度的标准描述（如"方案采用了先进的技术架构"）
        """
        return self.similarity(text, dimension_description)


# 各评价维度的标准描述模板
DIMENSION_DESCRIPTIONS = {
    "技术先进性": "该方案采用了先进的信息技术架构，包括云计算、大数据、人工智能、微服务、容器化等前沿技术，具有技术创新性和前瞻性。",
    "内容丰富度": "该方案内容完整，包含项目背景、需求分析、技术方案、实施计划、预算明细、风险评估等标准章节，逻辑清晰，表述详尽。",
    "预算合理性": "方案预算编制合理，各项费用明细清晰，成本估算有依据，符合项目规模和行业标准，性价比高。",
    "安全可靠性": "方案充分考虑了信息安全问题，包含等保合规设计、数据加密、安全审计、访问控制、容灾备份等措施，安全可靠。",
    "项目可行性": "方案技术可行、经济合理、实施有保障，团队配置合理，工期安排科学，风险管理到位，具有可操作性。",
}

def semantic_score(text, dimension, analyzer=None):
    """
    使用语义模型计算方案在某一维度的得分
    
    Args:
        text: 方案文本
        dimension: 维度名称（如"技术先进性"）
        analyzer: SemanticAnalyzer 实例（如果为None则创建新实例）
    
    Returns:
        float: 语义相似度得分 0-1
    """
    if dimension not in DIMENSION_DESCRIPTIONS:
        return 0.5
    
    if analyzer is None:
        analyzer = SemanticAnalyzer()
    
    description = DIMENSION_DESCRIPTIONS[dimension]
    return analyzer.similarity(text, description)


def batch_semantic_scores(text, analyzer=None):
    """
    批量计算所有维度的语义得分
    
    Returns:
        dict: {维度名称: 得分}
    """
    if analyzer is None:
        analyzer = SemanticAnalyzer()
    
    scores = {}
    for dimension, description in DIMENSION_DESCRIPTIONS.items():
        scores[dimension] = analyzer.similarity(text, description)
    
    return scores


def semantic_tech_score(text, analyzer=None):
    """
    专门的技术先进性语义评分
    对比方案与优秀技术方案的语义相似度
    """
    tech_keywords = [
        "采用微服务架构，支持弹性伸缩和高可用",
        "使用容器化部署，实现持续集成和持续交付",
        "引入人工智能和大数据分析能力",
        "采用分布式架构，支持海量数据处理",
    ]
    
    if analyzer is None:
        analyzer = SemanticAnalyzer()
    
    text_vec = analyzer.encode(text)
    if text_vec is None:
        return 0.5
    
    scores = []
    for kw in tech_keywords:
        kw_vec = analyzer.encode(kw)
        sim = util.pytorch_cos_sim(text_vec, kw_vec).item()
        scores.append(sim)
    
    return max(scores) if scores else 0.5


# 测试代码
if __name__ == "__main__":
    analyzer = SemanticAnalyzer()
    
    # 测试文本
    test_text = """
    本项目采用云计算技术，基于微服务架构设计，使用容器化部署方式。
    系统具备弹性伸缩能力，支持高并发访问。同时引入人工智能算法进行数据分析。
    """
    
    # 计算技术先进性得分
    score = semantic_tech_score(test_text, analyzer)
    print(f"技术先进性语义得分: {score:.4f}")
    
    # 批量计算各维度得分
    scores = batch_semantic_scores(test_text, analyzer)
    for dim, s in scores.items():
        print(f"{dim}: {s:.4f}")
