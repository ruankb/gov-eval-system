"""
PDF 报告生成模块
使用 reportlab，纯英文/ASCII 输出，避免中文字体问题
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import re


def clean_text(text):
    """清理文本，移除或替换非 ASCII 字符"""
    if text is None:
        return ""
    # 将常见中文标点替换为英文
    text = str(text)
    text = text.replace('，', ', ').replace('。', '. ').replace('；', '; ')
    text = text.replace('：', ': ').replace('！', '! ').replace('？', '? ')
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    # 只保留 ASCII 字符（字母、数字、基本符号）
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    # 合并多个空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def generate_evaluation_report(filename, project_name, project_type, project_scale,
                               security_level, total_score, scores, alerts, risks,
                               extracted_budget, text_length):
    """生成 PDF 评价报告（纯英文/ASCII 版本）"""
    
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # 自定义样式
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                 fontSize=20, textColor=colors.HexColor('#1a5276'),
                                 spaceAfter=30, alignment=1)  # 居中
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                   fontSize=14, textColor=colors.HexColor('#1a5276'),
                                   spaceBefore=12, spaceAfter=6)
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'],
                                  fontSize=10, leading=14)
    small_style = ParagraphStyle('Small', parent=styles['Normal'],
                                 fontSize=8, leading=10, textColor=colors.grey)
    
    story = []
    
    # ========== 标题 ==========
    story.append(Paragraph("Government Project Evaluation Report", title_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", small_style))
    story.append(Spacer(1, 0.5*cm))
    
    # ========== 1. Project Information ==========
    story.append(Paragraph("1. Project Information", heading_style))
    
    info_data = [
        ["Project Name", clean_text(project_name)],
        ["Project Type", clean_text(project_type)],
        ["Project Scale", clean_text(project_scale)],
        ["Security Level", clean_text(security_level)],
        ["Extracted Budget", f"{extracted_budget} (10K RMB)" if extracted_budget else "Not detected"],
        ["Text Length", f"{text_length} characters"],
        ["Total Score", f"{total_score:.2f}"],
    ]
    
    info_table = Table(info_data, colWidths=[4*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0fe')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))
    
    # ========== 2. Dimension Scores ==========
    story.append(Paragraph("2. Dimension Scores", heading_style))
    
    # 中英文映射
    name_map = {
        "技术先进性": "Technical Advanced",
        "内容丰富度": "Content Richness",
        "预算合理性": "Budget Reasonableness",
        "安全可靠性": "Security & Reliability",
        "与优秀方案相似度": "Similarity to Excellent",
        "项目可行性": "Project Feasibility"
    }
    
    score_data = [["Dimension", "Score", "Details"]]
    for indicator, data in scores.items():
        en_name = name_map.get(indicator, clean_text(indicator))
        score = data["得分"]
        detail = clean_text(data["说明"])[:120]
        score_data.append([en_name, f"{score:.2f}", detail])
    
    score_table = Table(score_data, colWidths=[4*cm, 2.5*cm, 7.5*cm])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.5*cm))
    
    # ========== 3. Risk Alerts ==========
    if risks:
        story.append(Paragraph("3. Risk Alerts", heading_style))
        for risk in risks[:6]:
            risk_text = f"• {clean_text(risk)}"
            if "预算" in risk or "Budget" in risk_text:
                story.append(Paragraph(f'<font color="#dc2626">{risk_text}</font>', normal_style))
            else:
                story.append(Paragraph(risk_text, normal_style))
        story.append(Spacer(1, 0.3*cm))
    
    # ========== 4. Improvement Suggestions ==========
    if alerts:
        story.append(Paragraph("4. Improvement Suggestions", heading_style))
        for alert in alerts[:6]:
            alert_text = f"• {clean_text(alert[:150])}"
            if "得分过低" in alert or "过低" in alert:
                story.append(Paragraph(f'<font color="#dc2626">{alert_text}</font>', normal_style))
            elif "得分一般" in alert:
                story.append(Paragraph(f'<font color="#ea580c">{alert_text}</font>', normal_style))
            else:
                story.append(Paragraph(alert_text, normal_style))
        story.append(Spacer(1, 0.3*cm))
    
    # ========== 5. Conclusion ==========
    story.append(Paragraph("5. Conclusion", heading_style))
    
    if total_score >= 0.8:
        conclusion_color = "#16a34a"
        conclusion = "Excellent: The solution meets all criteria, highly recommended."
    elif total_score >= 0.6:
        conclusion_color = "#ea580c"
        conclusion = "Good: The solution is acceptable with minor improvements needed."
    elif total_score >= 0.4:
        conclusion_color = "#dc2626"
        conclusion = "Fair: The solution has significant gaps, major revision recommended."
    else:
        conclusion_color = "#dc2626"
        conclusion = "Poor: The solution does not meet requirements, not recommended."
    
    story.append(Paragraph(f'<font color="{conclusion_color}"><b>{conclusion}</b></font>', normal_style))
    
    # 生成 PDF
    doc.build(story)
    return filename
