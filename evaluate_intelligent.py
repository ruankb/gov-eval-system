import re
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ========== 语义组配置 ==========
SEMANTIC_GROUPS = {
    "云计算技术": ["云计算", "云平台", "云服务", "弹性计算", "容器化", "云原生", "上云", "用云"],
    "边缘计算技术": ["边缘计算", "端计算", "靠近计算", "边缘节点", "边缘智能"],
    "人工智能技术": ["AI", "人工智能", "机器学习", "深度学习", "神经网络", "智能算法", "大模型"],
    "大数据技术": ["大数据", "数据挖掘", "数据分析", "数据仓库", "数据湖", "数据治理"],
    "物联网技术": ["物联网", "IoT", "物联", "传感器网络", "设备接入"],
    "安全技术": ["等保三级", "安全审计", "防火墙", "入侵检测", "数据加密", "隐私保护"],
    "区块链技术": ["区块链", "分布式账本", "智能合约", "共识机制", "去中心化"],
    "5G技术": ["5G", "第五代移动通信", "低延迟", "高带宽", "海量连接"],
    "DevOps技术": ["DevOps", "持续集成", "持续交付", "CI/CD", "自动化运维"],
    "微服务架构": ["微服务", "Spring Cloud", "服务网格", "Service Mesh", "API网关"],
}

# ========== 否定词检测 ==========
NEGATION_WORDS = ["不", "无需", "无须", "不需要", "不用", "不是", "没有", "无", "免"]

def check_negation(text, keyword):
    if not keyword:
        return False
    escaped_kw = re.escape(keyword)
    pattern1 = rf'(?:{"|".join(NEGATION_WORDS)})\s{{0,5}}{escaped_kw}'
    pattern2 = rf'{escaped_kw}\s{{0,5}}(?:{"|".join(NEGATION_WORDS)})'
    try:
        if re.search(pattern1, text, re.IGNORECASE):
            return True
        if re.search(pattern2, text, re.IGNORECASE):
            return True
    except re.error:
        pass
    return False

# ========== 同义词扩展 ==========
SYNONYMS = {
    "云计算": ["云", "云计算", "云平台", "云服务", "上云", "云化"],
    "边缘计算": ["边缘计算", "端计算", "边缘节点", "边缘端"],
    "大数据": ["大数据", "海量数据", "数据挖掘", "数据分析"],
    "人工智能": ["人工智能", "AI", "机器学习", "深度学习", "神经网络"],
    "物联网": ["物联网", "IoT", "物联", "传感器网络"],
    "等保三级": ["等保三级", "三级等保", "等级保护三级"],
    "安全审计": ["安全审计", "日志审计", "操作审计"],
}

def expand_synonyms(keyword):
    keyword_lower = keyword.lower()
    for base, syns in SYNONYMS.items():
        if keyword_lower in [s.lower() for s in syns] or keyword_lower == base.lower():
            return syns
    return [keyword]

def keyword_match_with_semantic(text, keyword):
    if check_negation(text, keyword):
        return False, f"被否定（{keyword}）"
    synonyms = expand_synonyms(keyword)
    text_lower = text.lower()
    for syn in synonyms:
        if syn.lower() in text_lower:
            return True, f"命中关键词：{syn}"
    return False, f"未命中关键词"

# ========== 1. 技术先进性评价 ==========
TECH_CATEGORIES = {
    "云计算与分布式": ["云计算", "云平台", "容器", "k8s", "docker", "分布式", "微服务"],
    "边缘计算与端智能": ["边缘计算", "端计算", "实时处理", "边缘节点"],
    "人工智能与机器学习": ["人工智能", "机器学习", "深度学习", "神经网络", "nlp"],
    "大数据技术": ["大数据", "数据挖掘", "数据分析", "数据仓库"],
    "物联网技术": ["物联网", "iot", "传感器", "设备接入"],
}

def evaluate_tech_advanced_with_details(text):
    text_lower = text.lower()
    best_score = 0.2
    best_category = ""
    matched_keywords = []
    
    for category, keywords in TECH_CATEGORIES.items():
        matched = []
        for kw in keywords:
            if not check_negation(text_lower, kw) and kw.lower() in text_lower:
                matched.append(kw)
        if matched:
            category_score = min(1.0, len(matched) / len(keywords) + 0.3)
            if category_score > best_score:
                best_score = category_score
                best_category = category
                matched_keywords = matched
    
    if best_category:
        detail = f"命中{best_category}类技术：{', '.join(matched_keywords)}"
    else:
        detail = "未检测到先进技术关键词"
    
    return best_score, detail

# ========== 2. 语义相似度 ==========
def load_sample_texts(sample_dir="优秀范文"):
    samples = []
    if not os.path.exists(sample_dir):
        return samples
    for f in os.listdir(sample_dir):
        if f.endswith('.txt'):
            try:
                with open(os.path.join(sample_dir, f), 'r', encoding='utf-8') as file:
                    samples.append(file.read())
            except:
                continue
    return samples

def semantic_similarity_score(text, sample_dir="优秀范文"):
    samples = load_sample_texts(sample_dir)
    if not samples:
        return 0.5, "无优秀范文可供对比"
    try:
        all_texts = [text] + samples
        vectorizer = TfidfVectorizer(max_features=1000)
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        current_vec = tfidf_matrix[0:1]
        similarities = []
        for i in range(1, len(all_texts)):
            sim = cosine_similarity(current_vec, tfidf_matrix[i:i+1])[0][0]
            similarities.append(sim)
        best_sim = max(similarities) if similarities else 0.5
        detail = f"与最优范文相似度：{best_sim:.2f}"
        return best_sim, detail
    except:
        return 0.5, "相似度计算失败"

# ========== 3. 安全等级 ==========
def infer_security_level(text):
    text_lower = text.lower()
    if check_negation(text_lower, "等保三级"):
        return "无特殊要求"
    if "等保三级" in text_lower or "三级等保" in text_lower:
        return "等保三级"
    elif "等保二级" in text_lower or "二级等保" in text_lower:
        return "等保二级"
    elif "安全审计" in text_lower or "防火墙" in text_lower:
        return "等保二级"
    else:
        return "无特殊要求"

def security_score_with_details(text, user_level, inferred_level):
    text_lower = text.lower()
    
    if user_level == "等保三级":
        if check_negation(text_lower, "等保三级"):
            return 0.0, "方案明确表示不需要等保三级，与您的要求冲突"
        if "等保三级" in text_lower or "三级等保" in text_lower:
            return 1.0, "方案明确提及等保三级，符合要求"
        return 0.0, "方案未提及等保三级，不符合您的要求"
    
    elif user_level == "等保二级":
        keywords = ["安全审计", "防火墙", "入侵检测", "访问控制"]
        matched = [kw for kw in keywords if kw in text_lower and not check_negation(text_lower, kw)]
        if not matched:
            return 0.0, f"未检测到基础安全措施，缺少：{', '.join(keywords)}"
        score = min(1.0, len(matched) / len(keywords) + 0.3)
        missing = [kw for kw in keywords if kw not in matched]
        detail = f"检测到安全措施：{', '.join(matched)}"
        if missing:
            detail += f"；缺失：{', '.join(missing)}"
        return score, detail
    
    else:
        basic_security_words = ["安全", "防护", "防火墙", "加密"]
        has_any_security = any(word in text_lower for word in basic_security_words)
        negative_words = ["不安全", "漏洞", "风险较高", "缺乏防护"]
        has_negative = any(word in text_lower for word in negative_words)
        
        if has_negative:
            return 0.3, "方案中提及安全风险，需要重视"
        elif has_any_security:
            return 1.0, "方案提到了安全措施，表现良好"
        else:
            return 0.8, "未提及安全相关内容（因无特殊要求，仅轻微扣分）"

# ========== 4. 内容丰富度 ==========
def evaluate_richness_with_details(text):
    sections = ["项目背景", "需求分析", "技术方案", "实施方案", "预算", "风险", "进度"]
    present_sections = [s for s in sections if s in text]
    missing_sections = [s for s in sections if s not in text]
    section_score = len(present_sections) / len(sections)
    length_score = min(1.0, len(text) / 5000)
    score = 0.6 * section_score + 0.4 * length_score
    
    detail = f"包含章节：{', '.join(present_sections)}"
    if missing_sections:
        detail += f"；缺失章节：{', '.join(missing_sections)}"
    detail += f"；文档字数：{len(text)}字符"
    
    return score, detail

# ========== 5. 预算合理性 ==========
def evaluate_budget_with_details(text, project_type, extracted_budget=None, user_budget_limit=None, project_scale="中型"):
    if extracted_budget is None:
        return 0.5, "未能从方案中提取到预算金额"
    
    scale_factors = {"小型": 0.3, "中型": 1.0, "大型": 2.0}
    scale_factor = scale_factors.get(project_scale, 1.0)
    
    if user_budget_limit is not None and user_budget_limit > 0:
        if extracted_budget <= user_budget_limit:
            usage_rate = extracted_budget / user_budget_limit
            if usage_rate >= 0.9:
                return 1.0, f"预算{extracted_budget}万元在您设定的上限{user_budget_limit}万元内，预算利用充分"
            elif usage_rate >= 0.7:
                return 0.95, f"预算{extracted_budget}万元在您设定的上限{user_budget_limit}万元内，预算合理"
            else:
                return 0.9, f"预算{extracted_budget}万元远低于上限{user_budget_limit}万元，预算充裕"
        else:
            exceed_ratio = (extracted_budget - user_budget_limit) / user_budget_limit
            score = max(0, 1 - exceed_ratio * 1.5)
            return score, f"预算{extracted_budget}万元超出您设定的上限{user_budget_limit}万元，超出{exceed_ratio:.1%}"
    
    budget_ranges = {
        "基础设施类": (50, 1000),
        "政务应用类": (20, 300),
        "数据智能类": (30, 500),
    }
    min_budget, max_budget = budget_ranges.get(project_type, (10, 500))
    min_budget_adj = min_budget * scale_factor
    max_budget_adj = max_budget * scale_factor
    
    if min_budget_adj <= extracted_budget <= max_budget_adj:
        return 1.0, f"预算{extracted_budget}万元在{project_scale}项目合理范围（{min_budget_adj:.0f}-{max_budget_adj:.0f}万元）内"
    elif extracted_budget < min_budget_adj:
        return 0.7, f"预算{extracted_budget}万元低于{project_scale}项目合理范围下限{min_budget_adj:.0f}万元，可能功能不足"
    else:
        exceed_ratio = (extracted_budget - max_budget_adj) / max_budget_adj
        score = max(0, 1 - exceed_ratio)
        return score, f"预算{extracted_budget}万元超出{project_scale}项目合理范围上限{max_budget_adj:.0f}万元，超出{exceed_ratio:.1%}"

# ========== 6. 可行性评分 ==========
def evaluate_feasibility(text):
    """评价方案可行性：技术可行性、经济可行性、实施可行性"""
    text_lower = text.lower()
    
    tech_keywords = ["技术架构", "系统设计", "开发框架", "技术选型", "技术方案"]
    tech_score = sum(1 for kw in tech_keywords if kw in text_lower) / max(1, len(tech_keywords))
    
    eco_keywords = ["投资回报", "ROI", "效益分析", "成本效益", "经济可行"]
    eco_score = sum(1 for kw in eco_keywords if kw in text_lower) / max(1, len(eco_keywords))
    
    imp_keywords = ["实施计划", "项目周期", "团队配置", "资源需求", "风险应对"]
    imp_score = sum(1 for kw in imp_keywords if kw in text_lower) / max(1, len(imp_keywords))
    
    total_score = 0.4 * tech_score + 0.3 * eco_score + 0.3 * imp_score
    detail = f"技术可行性:{tech_score:.2f}, 经济可行性:{eco_score:.2f}, 实施可行性:{imp_score:.2f}"
    
    return total_score, detail

# ========== 7. 风险识别 ==========
def detect_risks(text, project_type, project_scale, user_security_level, extracted_budget, user_budget_limit):
    risks = []
    text_lower = text.lower()
    
    if extracted_budget and user_budget_limit is None:
        scale_budget_map = {"小型": 30, "中型": 100, "大型": 300}
        expected_min = scale_budget_map.get(project_scale, 100)
        if extracted_budget < expected_min * 0.5:
            risks.append(f"💰 预算风险：预算{extracted_budget}万元显著低于{project_scale}项目常规水平（约{expected_min}万元），可能存在功能缺失风险")
    
    if user_security_level == "等保三级":
        if "等保三级" not in text_lower and "三级等保" not in text_lower:
            risks.append(f"🔒 合规风险：您选择了等保三级，但方案中未提及等保三级要求，存在合规风险")
    
    if "进度" not in text_lower and "里程碑" not in text_lower and "工期" not in text_lower:
        risks.append(f"📅 实施风险：方案未提供项目进度计划或里程碑节点，实施可控性存疑")
    
    if ("对接" in text_lower or "接口" in text_lower or "集成" in text_lower):
        if "接口规范" not in text_lower and "API" not in text_lower and "数据交换" not in text_lower:
            risks.append(f"🔗 集成风险：方案提到需要对接外部系统，但未说明接口规范或技术方案")
    
    empty_promises = ["确保", "保证", "一定", "绝对"]
    found_promises = [p for p in empty_promises if p in text_lower]
    if found_promises and len(text) < 3000:
        risks.append(f"⚠️ 可信度风险：方案使用了绝对化表述，但文档内容较简略，建议补充具体措施")
    
    if "边缘计算" in text_lower and ("云端" in text_lower or "云平台" in text_lower):
        if "协同" not in text_lower and "同步" not in text_lower:
            risks.append(f"🔄 技术风险：方案同时提及边缘计算和云计算，但未说明两者协同机制")
    
    return risks

# ========== 8. 综合评价 ==========
def evaluate_intelligent(text, project_type, user_security_level, project_scale="中型", budget_limit=None):
    extracted_budget = extract_budget(text)
    
    tech_score, tech_detail = evaluate_tech_advanced_with_details(text)
    richness_score, richness_detail = evaluate_richness_with_details(text)
    budget_score, budget_detail = evaluate_budget_with_details(text, project_type, extracted_budget, budget_limit, project_scale)
    sim_score, sim_detail = semantic_similarity_score(text)
    inferred_level = infer_security_level(text)
    security_score_val, security_detail = security_score_with_details(text, user_security_level, inferred_level)
    feasibility_score, feasibility_detail = evaluate_feasibility(text)
    
    scores = {
        "技术先进性": {"得分": tech_score, "说明": tech_detail},
        "内容丰富度": {"得分": richness_score, "说明": richness_detail},
        "预算合理性": {"得分": budget_score, "说明": budget_detail},
        "与优秀方案相似度": {"得分": sim_score, "说明": sim_detail},
        "安全可靠性": {"得分": security_score_val, "说明": security_detail},
        "项目可行性": {"得分": feasibility_score, "说明": feasibility_detail},
    }
    
    weights = {
        "技术先进性": 0.20,
        "内容丰富度": 0.15,
        "预算合理性": 0.15,
        "安全可靠性": 0.20,
        "与优秀方案相似度": 0.10,
        "项目可行性": 0.20,
    }
    
    total = 0
    total_weight = 0
    alerts = []
    missing_keywords_detail = {}
    
    for indicator, data in scores.items():
        w = weights.get(indicator, 0.1)
        score = data["得分"]
        total += score * w
        total_weight += w
        
        if score < 0.3:
            alerts.append(f"⚠️ {indicator}得分过低（{score:.2f}）")
        elif score < 0.6:
            alerts.append(f"📌 {indicator}得分一般（{score:.2f}）")
        elif score >= 0.8:
            alerts.append(f"✅ {indicator}表现优秀（{score:.2f}）")
    
    tech_missing = []
    for category, keywords in TECH_CATEGORIES.items():
        for kw in keywords:
            if kw not in text.lower() and not check_negation(text.lower(), kw):
                tech_missing.append(kw)
    missing_keywords_detail["技术先进性"] = tech_missing[:5]
    
    security_keywords = ["等保三级", "安全审计", "防火墙", "入侵检测", "数据加密"]
    security_missing = [kw for kw in security_keywords if kw not in text.lower()]
    missing_keywords_detail["安全可靠性"] = security_missing
    
    sections = ["项目背景", "需求分析", "技术方案", "实施方案", "预算", "风险"]
    section_missing = [s for s in sections if s not in text]
    missing_keywords_detail["内容丰富度"] = section_missing
    
    if user_security_level != inferred_level and user_security_level != "无特殊要求":
        alerts.append(f"🔒 安全等级提醒：您选择了{user_security_level}，系统推断可能为{inferred_level}")
    
    total = total / total_weight if total_weight > 0 else 0
    risks = detect_risks(text, project_type, project_scale, user_security_level, extracted_budget, budget_limit)
    
    return scores, total, alerts, extracted_budget, inferred_level, risks, missing_keywords_detail

# ========== 辅助函数 ==========
def extract_budget(text):
    patterns = [
        r'总投资\s*(\d+(?:\.\d+)?)\s*万元',
        r'项目预算\s*(\d+(?:\.\d+)?)\s*万元',
        r'预算\s*(\d+(?:\.\d+)?)\s*万元',
        r'总金额\s*(\d+(?:\.\d+)?)\s*万元',
        r'经费\s*(\d+(?:\.\d+)?)\s*万元',
        r'(\d+(?:\.\d+)?)\s*万元'
    ]
    for pattern in patterns:
        try:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        except:
            continue
    return None