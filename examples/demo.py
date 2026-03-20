#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""实际效果演示"""
import sys
sys.path.insert(0, '.')

from backend.app.nlp.parser import PDFParser
from backend.app.nlp.anti_hallucination import AntiHallucinationChecker, ConfidenceLevel

print("="*70)
print("金融研报助手 - 实际效果演示")
print("="*70)

# 1. PDF 解析
print("\n【步骤 1】解析 PDF 文件")
print("-"*70)
parser = PDFParser()
result = parser.parse('data/raw/test.pdf')

print(f"文件：北方稀土研报")
print(f"标题：{result['title']}")
print(f"页数：{result['page_count']} 页")
print(f"内容长度：{len(result['content'])} 字符")
print(f"表格数量：{len(result['tables'])} 个")
print(f"元数据：{result.get('metadata', {})}")

# 2. 反幻觉检查
print("\n【步骤 2】反幻觉检查")
print("-"*70)
checker = AntiHallucinationChecker()

# 从前 3 页提取实体
sample_pages = result['content'][:5000]
entities = checker.extract_with_evidence(sample_pages, page=1)
entities = checker.cross_validate(entities)
report = checker.generate_report(entities)

print(f"\n提取结果统计:")
print(f"  总实体数：{report['total_entities']}")
print(f"  高置信度：{report['high_confidence']} 个 ✅")
print(f"  中置信度：{report['medium_confidence']} 个 ⚠️")
print(f"  低置信度：{report['low_confidence']} 个 ❌")
print(f"  需要复核：{len(report['needs_review'])} 个 🔄")

print(f"\n幻觉风险等级：{report['low_confidence']}")
if report['low_confidence'] == 0:
    print("✅ 低风险 - 可以安全使用")
elif report['low_confidence'] < 3:
    print("⚠️ 中风险 - 部分需要复核")
else:
    print("❌ 高风险 - 建议人工审核")

# 3. 展示具体实体
print("\n【步骤 3】提取的实体（带证据）")
print("-"*70)

for entity_type, type_entities in report['entities_by_type'].items():
    print(f"\n{entity_type}:")
    for entity in type_entities[:5]:  # 只显示前 5 个
        confidence_emoji = {
            'high': '✅',
            'medium': '⚠️',
            'low': '❌',
            'unknown': '🔄'
        }.get(entity['confidence'], '⚠️')
        
        print(f"\n  {confidence_emoji} 值：{entity['value']}")
        print(f"     置信度：{entity['confidence']}")
        print(f"     需复核：{'是' if entity['needs_review'] else '否'}")
        print(f"     已交叉验证：{'是' if entity['cross_validated'] else '否'}")
        
        # 显示证据
        if entity['evidence']:
            ev = entity['evidence'][0]
            print(f"     来源：第{ev['page']}页")
            print(f"     原文：{ev['text'][:100]}...")

# 4. 最终报告
print("\n" + "="*70)
print("最终可信度报告")
print("="*70)

high_ratio = report['high_confidence'] / max(report['total_entities'], 1)
print(f"高置信度比例：{high_ratio:.1%}")
print(f"幻觉风险等级：{'LOW' if report['low_confidence'] == 0 else 'MEDIUM' if report['low_confidence'] < 3 else 'HIGH'}")

if high_ratio >= 0.9:
    print("\n✅ 报告质量优秀，可以安全使用")
elif high_ratio >= 0.7:
    print("\n⚠️ 报告质量良好，部分需要复核")
else:
    print("\n❌ 报告质量一般，建议人工审核")

print("\n" + "="*70)
print("测试完成！")
print("="*70)
