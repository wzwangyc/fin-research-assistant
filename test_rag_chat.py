#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG + 智能问答完整测试
"""
import sys
sys.path.insert(0, '.')

from backend.app.nlp.complete_parser import CompletePDFParser
from backend.app.llm.rag import RAGEngine
from backend.app.llm.chatbot import ResearchChatBot

print("="*70)
print("RAG + 智能问答完整测试")
print("="*70)

# 1. 解析 PDF
print("\n【步骤 1】解析 PDF 文档")
print("-"*70)
parser = CompletePDFParser(use_ocr=False)
doc = parser.parse('data/raw/test.pdf')

print(f"✅ 解析完成")
print(f"   页数：{doc.total_pages}")
print(f"   文本长度：{len(doc.all_text)}")
print(f"   表格数量：{len(doc.all_tables)}")

# 2. 加载到 RAG 引擎
print("\n【步骤 2】加载到 RAG 引擎")
print("-"*70)
rag = RAGEngine()
rag.load_document(doc.all_text)

print(f"✅ RAG 引擎已加载")
print(f"   文本块数量：{len(rag.chunks)}")

# 3. 创建问答机器人
print("\n【步骤 3】创建智能问答机器人")
print("-"*70)
bot = ResearchChatBot()
bot.load_document(doc.all_text)

print(f"✅ 问答机器人已就绪")

# 4. 测试问答
print("\n【步骤 4】测试智能问答")
print("="*70)

test_questions = [
    "北方稀土的股票代码是多少？",
    "研报给出的评级是什么？",
    "目标估值区间是多少？",
    "2021-2023 年的盈利预测？",
    "公司的核心竞争优势有哪些？",
    "主要风险因素是什么？"
]

for i, question in enumerate(test_questions, 1):
    print(f"\n【问题{i}】{question}")
    print("-"*70)
    
    result = bot.chat(question)
    
    print(f"回答：{result['answer'][:300]}...")
    print(f"置信度：{result['confidence']}")
    print(f"来源数量：{len(result['sources'])}")
    
    if result['sources']:
        print(f"来源示例：")
        source = result['sources'][0]
        print(f"  - 第{source['page']}页：{source['text'][:100]}...")
    
    if result.get('follow_up'):
        print(f"推荐追问：{result['follow_up']}")

# 5. 生成研报摘要
print("\n" + "="*70)
print("【步骤 5】生成研报摘要")
print("="*70)

summary = bot.summarize()
for question, answer in summary.items():
    print(f"\n❓ {question}")
    print(f"📝 {answer[:200]}...")

# 6. 导出对话
print("\n" + "="*70)
print("【步骤 6】导出对话记录")
print("="*70)

bot.export_conversation('data/processed/test_pdf/conversation.json')

print("\n" + "="*70)
print("✅ 测试完成！")
print("="*70)
