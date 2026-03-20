#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
金融研报助手 - 全流程演示
从 PDF 解析 → RAG 检索 → 智能问答 → 导出报告
"""
import sys
import json
from datetime import datetime
sys.path.insert(0, '.')

from backend.app.nlp.complete_parser import CompletePDFParser
from backend.app.llm.chatbot import ResearchChatBot
from backend.app.nlp.anti_hallucination import AntiHallucinationChecker

print("="*70)
print("📊 金融研报助手 - 全流程演示")
print("="*70)
print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"测试文件：北方稀土 (600111) 深度报告.pdf")
print("="*70)

# ==================== 步骤 1：PDF 完整解析 ====================
print("\n" + "="*70)
print("【步骤 1】PDF 完整解析")
print("="*70)

parser = CompletePDFParser(use_ocr=False)
doc = parser.parse('data/raw/test.pdf')

print(f"\n✅ 解析完成！")
print(f"   📄 总页数：{doc.total_pages} 页")
print(f"   📝 全文长度：{len(doc.all_text)} 字符")
print(f"   📊 表格数量：{len(doc.all_tables)} 个")
print(f"   📋 元数据：{doc.metadata}")

# 保存解析结果
parser.save_to_files(doc, 'data/processed/demo')
print(f"\n💾 文件已保存到：data/processed/demo/")

# ==================== 步骤 2：反幻觉检查 ====================
print("\n" + "="*70)
print("【步骤 2】反幻觉检查")
print("="*70)

checker = AntiHallucinationChecker()
entities = checker.extract_with_evidence(doc.all_text[:5000], page=1)
entities = checker.cross_validate(entities)
report = checker.generate_report(entities)

print(f"\n📊 实体识别统计:")
print(f"   总实体数：{report['total_entities']}")
print(f"   高置信度：{report['high_confidence']} ✅")
print(f"   中置信度：{report['medium_confidence']} ⚠️")
print(f"   低置信度：{report['low_confidence']} ❌")
print(f"   需要复核：{len(report['needs_review'])} 🔄")

high_ratio = report['high_confidence'] / max(report['total_entities'], 1)
print(f"\n🎯 高置信度比例：{high_ratio:.1%}")
print(f"🛡️ 幻觉风险等级：{'LOW ✅' if report['low_confidence'] == 0 else 'MEDIUM ⚠️' if report['low_confidence'] < 3 else 'HIGH ❌'}")

# ==================== 步骤 3：加载 RAG 引擎 ====================
print("\n" + "="*70)
print("【步骤 3】加载 RAG 检索引擎")
print("="*70)

bot = ResearchChatBot()
bot.load_document(doc.all_text)

print(f"\n✅ RAG 引擎已加载！")
print(f"   📚 文本块数量：{len(bot.rag.chunks)}")
print(f"   🔍 搜索模式：混合搜索（向量 + 关键词）")

# ==================== 步骤 4：智能问答测试 ====================
print("\n" + "="*70)
print("【步骤 4】智能问答测试")
print("="*70)

test_questions = [
    "北方稀土的股票代码是多少？",
    "研报给出的投资评级是什么？",
    "目标估值区间是多少？",
    "2021-2023 年的盈利预测？",
    "公司的核心竞争优势有哪些？",
    "主要风险因素是什么？"
]

answers = []

for i, question in enumerate(test_questions, 1):
    print(f"\n【问题{i}】{question}")
    print("-"*70)
    
    result = bot.chat(question)
    
    print(f"🤖 回答：{result['answer'][:300]}...")
    print(f"📊 置信度：{result['confidence']}")
    print(f"📚 来源数量：{len(result['sources'])}")
    
    if result['sources']:
        print(f"📄 来源示例：第{result['sources'][0]['page']}页")
    
    if result.get('follow_up'):
        print(f"💡 推荐追问：{result['follow_up']}")
    
    # 保存答案
    answers.append({
        'question': question,
        'answer': result['answer'],
        'confidence': result['confidence'],
        'sources_count': len(result['sources'])
    })

# ==================== 步骤 5：生成研报摘要 ====================
print("\n" + "="*70)
print("【步骤 5】自动生成研报摘要")
print("="*70)

summary = bot.summarize()

for question, answer in summary.items():
    print(f"\n❓ {question}")
    print(f"📝 {answer[:200]}...")

# ==================== 步骤 6：导出完整报告 ====================
print("\n" + "="*70)
print("【步骤 6】导出完整报告")
print("="*70)

# 1. 导出对话记录
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
conversation_file = f'data/processed/demo/conversation_{timestamp}.json'
bot.export_conversation(conversation_file)

# 2. 导出问答结果
results_file = f'data/processed/demo/qa_results_{timestamp}.json'
with open(results_file, 'w', encoding='utf-8') as f:
    json.dump({
        'document': {
            'title': doc.title,
            'pages': doc.total_pages,
            'text_length': len(doc.all_text),
            'tables': len(doc.all_tables)
        },
        'anti_hallucination': {
            'total_entities': report['total_entities'],
            'high_confidence': report['high_confidence'],
            'hallucination_risk': 'LOW' if report['low_confidence'] == 0 else 'MEDIUM'
        },
        'qa_results': answers,
        'summary': summary
    }, f, ensure_ascii=False, indent=2)

# 3. 导出统计报告
stats_file = f'data/processed/demo/statistics_{timestamp}.json'
with open(stats_file, 'w', encoding='utf-8') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'processing_time': 'N/A',
        'pdf_pages': doc.total_pages,
        'text_length': len(doc.all_text),
        'tables_count': len(doc.all_tables),
        'chunks_count': len(bot.rag.chunks),
        'questions_answered': len(answers),
        'avg_confidence': sum(1 for a in answers if a['confidence'] == 'high') / len(answers) if answers else 0
    }, f, ensure_ascii=False, indent=2)

print(f"\n✅ 报告已导出！")
print(f"   💬 对话记录：{conversation_file}")
print(f"   📊 问答结果：{results_file}")
print(f"   📈 统计报告：{stats_file}")

# ==================== 步骤 7：生成最终总结 ====================
print("\n" + "="*70)
print("【步骤 7】最终总结")
print("="*70)

print(f"""
📊 处理统计:
   • PDF 页数：{doc.total_pages} 页
   • 全文长度：{len(doc.all_text)} 字符
   • 表格数量：{len(doc.all_tables)} 个
   • RAG 文本块：{len(bot.rag.chunks)} 块
   • 回答问题：{len(answers)} 个

🛡️ 质量评估:
   • 实体总数：{report['total_entities']} 个
   • 高置信度：{report['high_confidence']} 个 ({high_ratio:.1%})
   • 幻觉风险：{'LOW ✅' if report['low_confidence'] == 0 else 'MEDIUM ⚠️'}
   • 需要复核：{len(report['needs_review'])} 个

✅ 功能验证:
   • PDF 解析：✅ 完成
   • 表格提取：✅ 完成 ({len(doc.all_tables)}个)
   • 反幻觉检查：✅ 完成
   • RAG 检索：✅ 完成
   • 智能问答：✅ 完成
   • 报告导出：✅ 完成
""")

print("\n" + "="*70)
print("🎉 全流程演示完成！")
print("="*70)
print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"输出目录：data/processed/demo/")
print("="*70)
