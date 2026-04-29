import pdfplumber
from docx import Document

def extract_text_from_pdf(pdf_path):
    """从PDF文件中提取文本"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"读取PDF出错：{e}")
    return text

def extract_text_from_docx(docx_path):
    """从Word文件中提取文本"""
    text = ""
    try:
        doc = Document(docx_path)
        for para in doc.paragraphs:
            if para.text:
                text += para.text + "\n"
    except Exception as e:
        print(f"读取Word出错：{e}")
    return text

def extract_text(file_path):
    """根据文件后缀自动选择提取函数"""
    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        return extract_text_from_docx(file_path)
    else:
        return "不支持的文件格式，请提供PDF或Word文档"

# ---------- 测试代码 ----------
if __name__ == "__main__":
    # 请修改下面的文件路径为你的测试文档路径
    test_file = "test1.docx"   # 如果你的文件名不同，请修改这里
    text = extract_text(test_file)
    
    # 打印前500个字符看看效果
    print("提取的文本预览（前500字符）：")
    print("-" * 50)
    print(text[:500])
    print("-" * 50)
    print(f"\n总字符数：{len(text)}")