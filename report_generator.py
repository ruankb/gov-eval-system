from fpdf import FPDF
import os
from datetime import datetime

def generate_evaluation_report(filename, project_name, project_type, project_scale,
                               security_level, total_score, scores, alerts, risks,
                               extracted_budget, text_length):
    """生成PDF评价报告 - 云端兼容版"""
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # 尝试加载中文字体（Linux 环境）
    font_loaded = False
    
    # Linux 常见中文字体路径
    linux_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    
    for font_path in linux_fonts:
        if os.path.exists(font_path):
            try:
                pdf.add_font('Chinese', '', font_path)
                font_loaded = True
                break
            except:
                continue
    
    if font_loaded:
        pdf.set_font('Chinese', '', 12)
    else:
        pdf.set_font('Helvetica', '', 10)
    
    # 标题
    pdf.set_font_size(16)
    pdf.cell(0, 10, "Government Project Evaluation Report", 0, 1, 'C')
    pdf.ln(5)
    
    # 生成时间
    pdf.set_font_size(9)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # 项目基本信息（使用拼音或英文）
    pdf.set_font_size(14)
    pdf.cell(0, 8, "1. Project Information", 0, 1)
    pdf.set_font_size(10)
    pdf.cell(0, 6, f"Project Name: {project_name}", 0, 1)
    pdf.cell(0, 6, f"Project Type: {project_type}", 0, 1)
    pdf.cell(0, 6, f"Project Scale: {project_scale}", 0, 1)
    pdf.cell(0, 6, f"Security Level: {security_level}", 0, 1)
    pdf.cell(0, 6, f"Extracted Budget: {extracted_budget} (10K RMB)" if extracted_budget else "Extracted Budget: Not detected", 0, 1)
    pdf.cell(0, 6, f"Text Length: {text_length} characters", 0, 1)
    pdf.cell(0, 6, f"Total Score: {total_score:.2f}", 0, 1)
    pdf.ln(5)
    
    # 各维度得分（使用英文）
    pdf.set_font_size(14)
    pdf.cell(0, 8, "2. Dimension Scores", 0, 1)
    pdf.set_font_size(10)
    
    # 中英文映射
    name_map = {
        "技术先进性": "Technical Advanced",
        "内容丰富度": "Content Richness", 
        "预算合理性": "Budget Reasonableness",
        "安全可靠性": "Security & Reliability",
        "与优秀方案相似度": "Similarity to Excellent",
        "项目可行性": "Project Feasibility"
    }
    
    for indicator, data in scores.items():
        en_name = name_map.get(indicator, indicator)
        score = data["得分"]
        detail = data["说明"][:80]
        
        pdf.set_font_size(11)
        pdf.cell(0, 6, f"{en_name}: {score:.2f}", 0, 1)
        pdf.set_font_size(9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"  {detail}", 0, 1)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
    
    pdf.ln(3)
    
    # 风险提示
    if risks:
        pdf.set_font_size(14)
        pdf.cell(0, 8, "3. Risk Alerts", 0, 1)
        pdf.set_font_size(10)
        for risk in risks[:5]:
            pdf.set_text_color(200, 0, 0)
            pdf.cell(5, 6, "-", 0, 0)
            pdf.set_text_color(0, 0, 0)
            short_risk = risk[:100] if len(risk) > 100 else risk
            pdf.cell(0, 6, f" {short_risk}", 0, 1)
        pdf.ln(3)
    
    # 改进建议
    if alerts:
        pdf.set_font_size(14)
        pdf.cell(0, 8, "4. Improvement Suggestions", 0, 1)
        pdf.set_font_size(10)
        for alert in alerts[:5]:
            pdf.cell(5, 6, "-", 0, 0)
            short_alert = alert[:100] if len(alert) > 100 else alert
            pdf.cell(0, 6, f" {short_alert}", 0, 1)
        pdf.ln(3)
    
    # 结论
    pdf.set_font_size(14)
    pdf.cell(0, 8, "5. Conclusion", 0, 1)
    pdf.set_font_size(11)
    
    if total_score >= 0.8:
        pdf.set_text_color(0, 150, 0)
        conclusion = "Excellent: The solution meets all criteria, highly recommended."
    elif total_score >= 0.6:
        pdf.set_text_color(200, 150, 0)
        conclusion = "Good: The solution is acceptable with minor improvements needed."
    elif total_score >= 0.4:
        pdf.set_text_color(200, 100, 0)
        conclusion = "Fair: The solution has significant gaps, major revision recommended."
    else:
        pdf.set_text_color(200, 0, 0)
        conclusion = "Poor: The solution does not meet requirements, not recommended."
    
    pdf.cell(0, 8, conclusion, 0, 1)
    
    # 保存
    pdf.output(filename)
    return filename
