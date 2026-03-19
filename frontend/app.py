#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Streamlit 前端界面"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.sql.etl import ResearchETL
from backend.app.sql.database import get_database


st.set_page_config(page_title="金融研报助手", page_icon="📊", layout="wide")


@st.cache_resource
def init_db():
    """初始化数据库"""
    db = get_database(use_sqlite=True)
    db.init_db("database/schema.sql")
    return db


@st.cache_resource
def get_etl():
    """获取 ETL 实例"""
    return ResearchETL()


def main():
    st.title("📊 金融研报助手")
    st.markdown("**NLP + LLM + SQL 智能研报分析**")
    
    # 侧边栏
    st.sidebar.header("⚙️ 控制面板")
    if st.sidebar.button("📁 初始化数据库"):
        init_db()
        st.sidebar.success("完成！")
    
    # 标签页
    tab1, tab2, tab3 = st.tabs(["📄 上传", "🔍 搜索", "💬 问答"])
    
    with tab1:
        render_upload()
    
    with tab2:
        render_search()
    
    with tab3:
        render_chat()


def render_upload():
    """上传标签页"""
    st.header("📄 研报上传")
    
    uploaded_file = st.file_uploader("上传 PDF", type=['pdf'])
    
    if uploaded_file:
        # 保存
        save_path = Path("data/raw") / uploaded_file.name
        save_path.parent.mkdir(exist_ok=True)
        
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"已保存：{save_path}")
        
        # 解析
        if st.button("🚀 解析"):
            with st.spinner("解析中..."):
                etl = get_etl()
                report_id = etl.process(str(save_path))
                
                if report_id > 0:
                    st.success(f"✅ 完成！ID: {report_id}")
                else:
                    st.error("❌ 失败")


def render_search():
    """搜索标签页"""
    st.header("🔍 搜索")
    
    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("公司", placeholder="贵州茅台")
    with col2:
        industry = st.selectbox("行业", ["全部", "科技", "金融", "消费"])
    
    if st.button("🔍 搜索"):
        st.info("开发中...")


def render_chat():
    """问答标签页"""
    st.header("💬 智能问答")
    
    question = st.text_input("问题", placeholder="茅台的投资价值？")
    
    if st.button("🤖 提问"):
        if not question:
            st.warning("请输入问题")
        else:
            with st.spinner("思考中..."):
                st.info("RAG+LLM 开发中...")
                st.write("基于研报内容，茅台的投资价值...")


if __name__ == "__main__":
    Path("data/raw").mkdir(exist_ok=True)
    main()
