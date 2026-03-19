#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Streamlit 智能问答界面
功能：
1. PDF 上传和解析
2. 智能问答
3. 引用溯源显示
4. 对话历史管理
"""

import streamlit as st
import json
import os
from datetime import datetime

# 导入我们的模块
from backend.app.nlp.complete_parser import CompletePDFParser
from backend.app.llm.chatbot import ResearchChatBot


def main():
    st.set_page_config(
        page_title="金融研报智能问答",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 金融研报智能问答系统")
    st.markdown("---")
    
    # 初始化 session state
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []
    if 'document_loaded' not in st.session_state:
        st.session_state.document_loaded = False
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # PDF 上传
        uploaded_file = st.file_uploader("上传 PDF 研报", type=['pdf'])
        
        if uploaded_file:
            with st.spinner("正在解析 PDF..."):
                # 保存上传的文件
                os.makedirs('data/uploaded', exist_ok=True)
                file_path = f'data/uploaded/{uploaded_file.name}'
                
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                # 解析 PDF
                parser = CompletePDFParser(use_ocr=False)
                doc = parser.parse(file_path)
                
                # 创建聊天机器人
                st.session_state.chatbot = ResearchChatBot()
                st.session_state.chatbot.load_document(doc.all_text)
                st.session_state.document_loaded = True
                
                st.success(f"✅ 解析完成！")
                st.info(f"📄 {doc.total_pages}页 | 📝 {len(doc.all_text)}字符 | 📊 {len(doc.all_tables)}个表格")
        
        st.markdown("---")
        
        # 对话管理
        if st.session_state.document_loaded:
            st.subheader("💬 对话管理")
            
            if st.button("🗑️ 清空对话"):
                st.session_state.chatbot.clear_history()
                st.session_state.conversation = []
                st.rerun()
            
            if st.button("💾 导出对话"):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'data/processed/conversation_{timestamp}.json'
                st.session_state.chatbot.export_conversation(filename)
                st.success(f"对话已导出：{filename}")
        
        st.markdown("---")
        st.markdown("**功能特点**:")
        st.markdown("- ✅ 完整 PDF 解析")
        st.markdown("- ✅ 智能问答")
        st.markdown("- ✅ 引用溯源")
        st.markdown("- ✅ 反幻觉机制")
    
    # 主界面
    if not st.session_state.document_loaded:
        st.info("👈 请先在左侧上传 PDF 研报")
        
        st.markdown("### 📋 使用步骤")
        st.markdown("""
        1. **上传 PDF** - 在左侧上传金融研报 PDF
        2. **等待解析** - 系统自动解析 PDF 内容
        3. **开始问答** - 在下方输入问题
        4. **查看来源** - 每个回答都有原文引用
        """)
        
        st.markdown("### 🎯 示例问题")
        st.markdown("""
        - 这家公司的股票代码是多少？
        - 研报给出的评级是什么？
        - 目标估值区间是多少？
        - 未来三年的盈利预测？
        - 公司的核心竞争优势？
        - 主要风险因素有哪些？
        """)
    else:
        # 显示对话历史
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.conversation:
                if message['role'] == 'user':
                    st.markdown(f"**👤 您**: {message['content']}")
                else:
                    st.markdown(f"**🤖 助手**: {message['content']}")
                    
                    # 显示来源
                    if message.get('sources'):
                        with st.expander(f"📄 查看引用来源 ({len(message['sources'])}个)"):
                            for i, source in enumerate(message['sources'], 1):
                                st.markdown(f"**来源{i}** (第{source['page']}页):")
                                st.markdown(f"> {source['text']}")
                    
                    # 显示置信度
                    confidence_emoji = {
                        'high': '✅',
                        'medium': '⚠️',
                        'low': '❌',
                        'unknown': '❓'
                    }.get(message.get('confidence', 'unknown'), '❓')
                    st.markdown(f"置信度：{confidence_emoji} {message.get('confidence', 'unknown')}")
                    
                    # 推荐追问
                    if message.get('follow_up'):
                        st.markdown("**💡 推荐追问**:")
                        for question in message['follow_up']:
                            st.markdown(f"- {question}")
                
                st.markdown("---")
        
        # 输入框
        st.markdown("### 💬 输入问题")
        
        # 预设问题
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 估值是多少？", use_container_width=True):
                st.session_state.user_input = "估值是多少？"
        with col2:
            if st.button("⭐ 评级是什么？", use_container_width=True):
                st.session_state.user_input = "评级是什么？"
        with col3:
            if st.button("⚠️ 风险有哪些？", use_container_width=True):
                st.session_state.user_input = "主要风险有哪些？"
        
        # 输入框
        user_input = st.text_input(
            "输入您的问题",
            key="input",
            placeholder="例如：北方稀土的核心竞争优势是什么？",
            label_visibility="collapsed"
        )
        
        # 处理用户输入
        if user_input or 'user_input' in st.session_state:
            query = user_input or st.session_state.user_input
            if 'user_input' in st.session_state:
                del st.session_state.user_input
            
            with st.spinner("正在思考..."):
                # 调用聊天机器人
                result = st.session_state.chatbot.chat(query)
                
                # 保存对话
                st.session_state.conversation.append({
                    'role': 'user',
                    'content': query
                })
                
                st.session_state.conversation.append({
                    'role': 'assistant',
                    'content': result['answer'],
                    'sources': result.get('sources', []),
                    'confidence': result.get('confidence', 'unknown'),
                    'follow_up': result.get('follow_up', [])
                })
                
                st.rerun()


if __name__ == '__main__':
    main()
