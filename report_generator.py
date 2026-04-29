from fpdf import FPDF
import os
from datetime import datetime

def generate_evaluation_report(filename, project_name, project_type, project_scale,
                               security_level, total_score, scores, alerts, risks,
                               extracted_budget, text_length):
    """生成PDF评价报告 - 超简化版"""
    
    # 创建PDF
    pdf = FPDF()
    pdf.add_page()
    
    # 设置自动分页
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # 尝试加载中文字体
    font_loaded = False
    font_paths = [
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msyh.ttc",
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdf.add_font('Chinese', '', font_path)
                font_loaded = True
                break
            except:
                continue
    
    # 设置字体
    if font_loaded:
        pdf.set_font('Chinese', '', 11)
    else:
        pdf.set_font('Helvetica', '', 10)
    
    # ========== 标题 ==========
    pdf.set_font_size(16)
    pdf.cell(0, 10, "政府信息化项目方案智能评价报告", 0, 1, 'C')
    pdf.ln(5)
    
    # ========== 生成时间 ==========
    pdf.set_font_size(9)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 6, f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # ========== 一、项目基本信息 ==========
    pdf.set_font_size(14)
    pdf.cell(0, 8, "一、项目基本信息", 0, 1)
    pdf.set_font_size(10)
    pdf.cell(0, 6, f"项目名称：{project_name}", 0, 1)
    pdf.cell(0, 6, f"项目类型：{project_type}", 0, 1)
    pdf.cell(0, 6, f"项目规模：{project_scale}", 0, 1)
    pdf.cell(0, 6, f"安全等级：{security_level}", 0, 1)
    pdf.cell(0, 6, f"提取预算：{extracted_budget}万元" if extracted_budget else "提取预算：未检测", 0, 1)
    pdf.cell(0, 6, f"方案字数：{text_length}字", 0, 1)
    pdf.cell(0, 6, f"加权总分：{total_score:.2f}", 0, 1)
    pdf.ln(5)
    
    # ========== 二、各维度得分 ==========
    pdf.set_font_size(14)
    pdf.cell(0, 8, "二、各维度得分详情", 0, 1)
    pdf.set_font_size(10)
    
    for indicator, data in scores.items():
        score = data["得分"]
        detail = data["说明"]
        
        pdf.set_font_size(11)
        pdf.cell(0, 6, f"{indicator}：{score:.2f}", 0, 1)
        
        pdf.set_font_size(9)
        pdf.set_text_color(100, 100, 100)
        # 处理长文本
        if len(detail) > 80:
            detail = detail[:80] + "..."
        pdf.cell(0, 5, f"  {detail}", 0, 1)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
    
    pdf.ln(3)
    
    # ========== 三、风险扫描 ==========
    if risks:
        pdf.set_font_size(14)
        pdf.cell(0, 8, "三、风险扫描结果", 0, 1)
        pdf.set_font_size(10)
        
        for risk in risks:
            pdf.set_text_color(200, 0, 0)
            pdf.cell(5, 6, "-", 0, 0)
            pdf.set_text_color(0, 0, 0)
            # 限制长度
            short_risk = risk[:150] if len(risk) > 150 else risk
            pdf.cell(0, 6, f" {short_risk}", 0, 1)
        pdf.ln(3)
    
    # ========== 四、改进建议 ==========
    if alerts:
        pdf.set_font_size(14)
        pdf.cell(0, 8, "四、改进建议", 0, 1)
        pdf.set_font_size(10)
        
        for alert in alerts[:6]:
            pdf.cell(5, 6, "-", 0, 0)
            short_alert = alert[:120] if len(alert) > 120 else alert
            pdf.cell(0, 6, f" {short_alert}", 0, 1)
        pdf.ln(3)
    
    # ========== 五、评价结论 ==========
    pdf.set_font_size(14)
    pdf.cell(0, 8, "五、评价结论", 0, 1)
    pdf.set_font_size(11)
    
    if total_score >= 0.8:
        pdf.set_text_color(0, 150, 0)
        conclusion = "方案质量优秀，各项指标表现良好，建议优先考虑。"
    elif total_score >= 0.6:
        pdf.set_text_color(200, 150, 0)
        conclusion = "方案质量良好，部分维度有提升空间，建议优化后采用。"
    elif total_score >= 0.4:
        pdf.set_text_color(200, 100, 0)
        conclusion = "方案质量一般，存在较多不足，建议重大修改后重新评审。"
    else:
        pdf.set_text_color(200, 0, 0)
        conclusion = "方案质量较差，不建议采用。"
    
    pdf.cell(0, 8, conclusion, 0, 1)
    
    # 保存
    pdf.output(filename)
    print(f"PDF已保存: {filename}")
    return filename