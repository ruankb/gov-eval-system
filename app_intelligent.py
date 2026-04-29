import streamlit as st
import pandas as pd
import plotly.express as px
import os
import tempfile
import json
from datetime import datetime
from extract_text import extract_text
from evaluate_intelligent import evaluate_intelligent, extract_budget, infer_security_level, SEMANTIC_GROUPS
from db_manager import init_db, save_evaluation, get_history, get_all_project_names, get_iteration_history
from report_generator import generate_evaluation_report

st.set_page_config(page_title="智评系统", page_icon="🏛️", layout="wide")

# ========== CSS样式 ==========
st.markdown("""
<style>
/* 页面整体背景 */
.stApp {
    background-color: #f0f2f6;
}

/* 侧边栏 */
[data-testid="stSidebar"] {
    background-color: #0f2b3d !important;
}
[data-testid="stSidebar"] * {
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stSelectbox select,
[data-testid="stSidebar"] .stNumberInput input {
    background-color: #1e4a6e !important;
    border: 1px solid #2c5a7a !important;
    color: white !important;
}
[data-testid="stSidebar"] .stButton button {
    background-color: #2c6e9e !important;
    color: white !important;
}

/* 主内容区文字黑色 */
.stMarkdown, .stText, p, div, span, label, h1, h2, h3, h4, h5, h6,
.stExpander *, .main-card *, .metric-container * {
    color: #000000 !important;
}

/* 卡片 */
.main-card {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid #d0d0d0;
    margin-bottom: 1rem;
}
.score-card {
    background: linear-gradient(135deg, #0f2b3d 0%, #1e4d76 100%);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}
.score-card * {
    color: white !important;
}
.metric-container {
    background-color: #fafafa;
    border-radius: 10px;
    padding: 0.8rem;
    margin: 0.5rem 0;
    border: 1px solid #d0d0d0;
}

/* Expander */
.stExpander {
    background-color: #ffffff !important;
    border: 1px solid #d0d0d0 !important;
    border-radius: 12px !important;
}
.stExpander summary {
    background-color: #f5f5f5 !important;
    border-radius: 10px;
}

/* 导出按钮 */
div.stDownloadButton > button {
    background-color: #1f77b4 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
}

/* 进度条 */
.stProgress > div > div > div > div {
    background-color: #0f2b3d;
}

/* 标签页 */
.stTabs [data-baseweb="tab-list"] {
    background-color: #ffffff;
    border-radius: 10px;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #0f2b3d !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# 初始化数据库
init_db()

# Session状态
if "evaluation_done" not in st.session_state:
    st.session_state.evaluation_done = False
if "current_results" not in st.session_state:
    st.session_state.current_results = []
if "current_project_name" not in st.session_state:
    st.session_state.current_project_name = ""
if "compare_mode" not in st.session_state:
    st.session_state.compare_mode = False
if "result_v2" not in st.session_state:
    st.session_state.result_v2 = None

def get_percentile_rank(score, ptype):
    history = get_history()
    scores = [h[7] for h in history if h[3] == ptype]
    if not scores:
        return None
    scores.sort()
    for i, s in enumerate(scores):
        if score <= s:
            return int(i / len(scores) * 100)
    return 100

def get_score_color(s):
    return "#2e7d32" if s >= 0.8 else "#ed6c02" if s >= 0.6 else "#d32f2f"

# ========== 侧边栏 ==========
with st.sidebar:
    st.markdown("### 🏛️ 政府信息化项目智能评价系统")
    st.markdown("---")
    
    project_name = st.text_input("项目名称", placeholder="可选")
    project_type = st.selectbox("项目类型", ["基础设施类", "政务应用类", "数据智能类"])
    project_scale = st.selectbox("项目规模", ["小型", "中型", "大型"])
    security_level = st.selectbox("安全等级", ["无特殊要求", "等保二级", "等保三级"])
    
    st.markdown("---")
    uploaded_files = st.file_uploader("方案文件", type=['pdf', 'docx'], accept_multiple_files=True)
    budget_limit = st.number_input("预算上限(万元)", min_value=0.0, step=10.0, value=0.0)
    budget_limit = budget_limit if budget_limit > 0 else None
    
    st.markdown("---")
    st.markdown("#### 🔄 方案迭代跟踪")
    iteration_mode = st.checkbox("迭代模式")
    iteration_name = None
    iteration_version = 1
    if iteration_mode:
        iteration_name = st.text_input("方案名称", placeholder="输入唯一标识")
        iteration_version = st.number_input("版本号", min_value=1, step=1, value=1)
    
    st.markdown("---")
    compare_mode = st.checkbox("📊 版本对比模式")
    v2_file = None
    if compare_mode:
        v2_file = st.file_uploader("修改版方案", type=['pdf', 'docx'], key="v2")
    
    run = st.button("🚀 开始评价", type="primary", use_container_width=True)

# ========== 评价执行 ==========
if run and uploaded_files:
    pname = project_name.strip() or f"项目_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.current_project_name = pname
    st.session_state.current_results = []
    st.session_state.compare_mode = compare_mode
    st.session_state.result_v2 = None
    
    progress = st.progress(0)
    for idx, f in enumerate(uploaded_files):
        ext = f.name.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(f.getbuffer())
            tmp_path = tmp.name
        text = extract_text(tmp_path)
        scores, total, alerts, budget_ext, inferred, risks, missing = evaluate_intelligent(
            text, project_type, security_level, project_scale, budget_limit
        )
        percentile = get_percentile_rank(total, project_type)
        st.session_state.current_results.append({
            "filename": f.name, "total": total, "scores": scores, "alerts": alerts,
            "risks": risks, "budget": budget_ext, "length": len(text),
            "percentile": percentile, "missing": missing, "text": text
        })
        save_evaluation(
            pname, project_type, project_scale, security_level,
            f.name, total, {k:v["得分"] for k,v in scores.items()},
            alerts, risks, budget_ext,
            iteration_name if iteration_mode else None,
            iteration_version if iteration_mode else None
        )
        os.unlink(tmp_path)
        progress.progress((idx+1)/len(uploaded_files))
    
    if compare_mode and v2_file:
        ext2 = v2_file.name.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext2}") as tmp:
            tmp.write(v2_file.getbuffer())
            tmp_path2 = tmp.name
        text2 = extract_text(tmp_path2)
        scores2, total2, alerts2, budget2, inferred2, risks2, missing2 = evaluate_intelligent(
            text2, project_type, security_level, project_scale, budget_limit
        )
        st.session_state.result_v2 = {
            "filename": v2_file.name, "total": total2, "scores": scores2,
            "alerts": alerts2, "risks": risks2, "budget": budget2,
            "length": len(text2), "missing": missing2
        }
        os.unlink(tmp_path2)
    
    st.session_state.evaluation_done = True
    st.rerun()

# ========== 显示结果 ==========
if st.session_state.evaluation_done and st.session_state.current_results:
    results = st.session_state.current_results
    pname = st.session_state.current_project_name
    
    st.markdown(f"<h2>📊 {pname}</h2>", unsafe_allow_html=True)
    st.caption(f"评价时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if len(results) > 1:
        tabs = st.tabs([f"📄 {r['filename'][:20]}" for r in results])
    else:
        tabs = [st.container()]
    
    for idx, r in enumerate(results):
        with tabs[idx]:
            cols = st.columns(4)
            with cols[0]:
                st.markdown(f"<div class='score-card'><div style='font-size:0.8rem'>综合评分</div><div style='font-size:2rem'>🌟 {r['total']:.2f}</div></div>", unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"<div class='main-card'><div>📝 字数</div><div style='font-size:1.5rem; font-weight:600'>{r['length']:,}</div></div>", unsafe_allow_html=True)
            with cols[2]:
                if r['budget']:
                    st.markdown(f"<div class='main-card'><div>💰 预算</div><div style='font-size:1.5rem; font-weight:600'>{r['budget']:.0f} 万</div></div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='main-card'><div>💰 预算</div><div style='font-size:1rem'>未检测</div></div>", unsafe_allow_html=True)
            with cols[3]:
                rank_text = f"超过 {r['percentile']}%" if r['percentile'] else "暂无"
                st.markdown(f"<div class='main-card'><div>📈 排名</div><div style='font-size:1.2rem; font-weight:600'>{rank_text}</div></div>", unsafe_allow_html=True)
            
            st.markdown("#### 📈 各维度得分")
            dims = list(r["scores"].items())
            dcols = st.columns(2)
            for i, (name, data) in enumerate(dims):
                s = data["得分"]
                with dcols[i%2]:
                    st.markdown(f"""
                    <div class='metric-container'>
                        <div style='display:flex;justify-content:space-between; margin-bottom:0.3rem'>
                            <span style='font-weight:500'>{name}</span>
                            <span style='font-weight:600; color:{get_score_color(s)}'>{s:.2f}</span>
                        </div>
                        <div style='background:#e0e0e0; border-radius:10px; height:6px'>
                            <div style='background:{get_score_color(s)}; width:{s*100}%; height:6px; border-radius:10px'></div>
                        </div>
                        <div style='font-size:0.7rem; color:#666; margin-top:0.3rem'>{data['说明'][:80]}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 具体修改建议
            with st.expander("📋 具体修改建议", expanded=True):
                sugg_cnt = 0
                missing = r.get("missing", {})
                
                if security_level == "等保三级" and r["scores"].get("安全可靠性", {}).get("得分", 1) < 0.5:
                    miss = missing.get("安全可靠性", [])
                    st.error(f"🔴 **安全可靠性** - 等保三级要求未满足\n\n缺失关键词：{', '.join(miss[:5]) if miss else '等保相关'}\n\n💡 建议：在方案中补充等保三级设计、安全审计、数据加密等内容")
                    sugg_cnt += 1
                
                if r["budget"] and budget_limit and r["budget"] > budget_limit:
                    st.warning(f"🟡 **预算合理性** - 超出上限 {r['budget'] - budget_limit:.1f}万元\n\n💡 建议：削减非核心功能开支，或分阶段实施")
                    sugg_cnt += 1
                
                if r["scores"].get("技术先进性", {}).get("得分", 1) < 0.4:
                    miss = missing.get("技术先进性", [])
                    st.warning(f"🟡 **技术先进性** - 得分较低\n\n缺失关键词：{', '.join(miss[:5]) if miss else '先进技术关键词'}\n\n💡 建议：引入云计算、大数据、AI等先进技术")
                    sugg_cnt += 1
                
                if r["scores"].get("内容丰富度", {}).get("得分", 1) < 0.5:
                    miss = missing.get("内容丰富度", [])
                    st.info(f"🟢 **内容丰富度** - 方案结构不完整\n\n缺失章节：{', '.join(miss) if miss else '标准章节'}\n\n💡 建议：补充项目背景、需求分析、技术方案、预算等内容")
                    sugg_cnt += 1
                
                if sugg_cnt == 0:
                    st.success("✅ 方案质量良好，无明显短板")
                
                if any(missing.values()):
                    st.markdown("**📋 快速检查清单**")
                    for ind, mlist in missing.items():
                        if mlist:
                            st.write(f"- {ind}：缺失 {', '.join(mlist[:5])}")
            
            # 风险提示
            if r["risks"]:
                with st.expander("⚠️ 风险提示"):
                    for risk in r["risks"]:
                        st.error(risk)
        
        # ===== 导出报告 =====
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            report_filename = f"报告_{pname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            generate_evaluation_report(report_filename, pname, project_type, project_scale,
                security_level, r["total"], r["scores"], r["alerts"],
                r["risks"], r["budget"], r["length"])
            with open(report_filename, "rb") as f:
                st.download_button(
                    label=f"📥 导出「{results[idx]['filename'][:30]}」评价报告",
                    data=f,
                    file_name=report_filename,
                    mime="application/pdf",
                    key=f"export_{idx}"
                )
    
    # 版本对比
    if st.session_state.compare_mode and st.session_state.result_v2:
        st.markdown("---")
        st.header("📊 版本对比分析")
        
        v2 = st.session_state.result_v2
        v1 = results[0]
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("原版总分", f"{v1['total']:.2f}")
        with c2:
            st.metric("修改版总分", f"{v2['total']:.2f}")
        with c3:
            delta = v2['total'] - v1['total']
            st.metric("变化", f"{delta:+.2f}", delta_color="normal")
        
        st.subheader("各维度得分对比")
        compare_data = []
        for name in v1["scores"].keys():
            old_s = v1["scores"][name]["得分"]
            new_s = v2["scores"][name]["得分"]
            compare_data.append({"指标": name, "原版": f"{old_s:.2f}", "修改版": f"{new_s:.2f}", "变化": f"{new_s - old_s:+.2f}"})
        st.dataframe(pd.DataFrame(compare_data), use_container_width=True)
        
        if delta > 0:
            st.success("🎉 修改有效！方案质量有所提升。")
        elif delta < 0:
            st.warning("⚠️ 修改版得分下降，建议重新审视修改内容。")

# ========== 迭代趋势图 ==========
if iteration_mode and iteration_name:
    history_versions = get_iteration_history(iteration_name)
    if history_versions and len(history_versions) > 1:
        st.markdown("---")
        st.subheader("📈 改进趋势")
        trend_data = pd.DataFrame([
            {"版本": v[0], "总分": v[1], "时间": v[2][:16]} for v in history_versions
        ])
        fig = px.line(trend_data, x="版本", y="总分", title="评分变化趋势", markers=True)
        st.plotly_chart(fig)
        
        first_score = history_versions[0][1]
        last_score = history_versions[-1][1]
        improvement = last_score - first_score
        if improvement > 0:
            st.success(f"🎉 相比初版提升了 {improvement:+.2f} 分！")
        else:
            st.warning(f"📉 相比初版变化 {improvement:+.2f} 分")

# ========== 历史记录 ==========
with st.expander("📜 历史评价记录"):
    st.markdown("""
    <style>
    /* 下拉框主体 */
    .stExpander [data-baseweb="select"] {
        background-color: #e6f3ff !important;
    }
    .stExpander [data-baseweb="select"] > div {
        background-color: #e6f3ff !important;
        border: 1px solid #b0d4f0 !important;
    }
    /* 全局选项面板 - 使用最高优先级 */
    [role="listbox"] {
        background-color: #e6f3ff !important;
        border: 1px solid #b0d4f0 !important;
    }
    [role="option"] {
        background-color: #e6f3ff !important;
        color: #000000 !important;
    }
    [role="option"]:hover {
        background-color: #d4e8ff !important;
    }
    /* 下拉框图标 */
    .stExpander svg {
        fill: #000000 !important;
        stroke: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    hist_proj = st.selectbox("选择项目", ["全部"] + get_all_project_names())
    
    if hist_proj:
        history = get_history(hist_proj if hist_proj != "全部" else None)
        if history:
            for h in history[:10]:
                st.markdown(f"""
                <div style="background-color:#e6f3ff; padding:0.8rem; border-radius:8px; margin-bottom:0.5rem; border:1px solid #b0d4f0;">
                    <strong>{h[1][:16]}</strong> | {h[2]} | {h[6][:30]} | 总分: <strong>{h[7]:.2f}</strong>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("暂无历史记录")