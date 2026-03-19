#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
金融研报助手 - 完整效果演示
对比普通解析 vs OCR 增强解析
"""
import sys
sys.path.insert(0, '.')

from backend.app.nlp.parser import PDFParser
from backend.app.nlp.parser_ocr import PDFParserWithOCR
from backend.app.nlp.anti_hallucination import AntiHallucinationChecker

print("="*70)
print("金融研报助手 - 完整效果演示")
print("="*70)

# 1. 普通解析
print("\n【方法 1】普通 PDF 解析")
print("-"*70)
parser = PDFParser()
result1 = parser.parse('data/raw/test.pdf')

print(f"解析方式：普通文本提取")
print(f"标题：{result1['title']}")
print(f"页数：{result1['page_count']}")
print(f"内容长度：{len(result1['content'])}")
print(f"表格数量：{len(result1['tables'])}")
print(f"元数据：{result1.get('metadata', {})}")

# 2. OCR 增强解析
print("\n【方法 2】OCR 增强解析")
print("-"*70)
parser_ocr = PDFParserWithOCR(use_ocr=False)  # 暂时不启用 OCR（需要安装库）
result2 = parser_ocr.parse('data/raw/test.pdf')

print(f"解析方式：{result2['parse_method']}")
print(f"标题：{result2['title']}")
print(f"页数：{result2['page_count']}")
print(f"内容长度：{len(result2['content'])}")
print(f"表格数量：{len(result2['tables'])}")
print(f"元数据：{result2.get('metadata', {})}")

# 3. 反幻觉检查
print("\n【方法 3】反幻觉检查")
print("-"*70)
checker = AntiHallucinationChecker()

# 使用 OCR 增强版的内容
entities = checker.extract_with_evidence(result2['content'][:5000], page=1)
entities = checker.cross_validate(entities)
report = checker.generate_report(entities)

print(f"\n提取统计:")
print(f"  总实体数：{report['total_entities']}")
print(f"  高置信度：{report['high_confidence']} ✅")
print(f"  中置信度：{report['medium_confidence']} ⚠️")
print(f"  低置信度：{report['low_confidence']} ❌")
print(f"  需要复核：{len(report['needs_review'])} 🔄")

# 4. 展示关键实体
print("\n【提取的关键信息】")
print("-"*70)

for entity_type, type_entities in report['entities_by_type'].items():
    print(f"\n{entity_type}:")
    for entity in type_entities[:5]:
        confidence_emoji = {'high': '✅', 'medium': '⚠️', 'low': '❌', 'unknown': '🔄'}.get(entity['confidence'], '⚠️')
        
        print(f"\n  {confidence_emoji} {entity['value']}")
        print(f"     置信度：{entity['confidence']}")
        print(f"     需复核：{'是' if entity['needs_review'] else '否'}")
        
        if entity['evidence']:
            ev = entity['evidence'][0]
            print(f"     来源：第{ev['page']}页")
            print(f"     原文：{ev['text'][:80]}...")

# 5. 最终评估
print("\n" + "="*70)
print("最终评估")
print("="*70)

high_ratio = report['high_confidence'] / max(report['total_entities'], 1)
print(f"高置信度比例：{high_ratio:.1%}")
print(f"幻觉风险等级：{'LOW' if report['low_confidence'] == 0 else 'MEDIUM' if report['low_confidence'] < 3 else 'HIGH'}")

if high_ratio >= 0.8 and report['low_confidence'] == 0:
    print("\n✅ 提取质量优秀，可以安全使用")
elif high_ratio >= 0.6:
    print("\n⚠️ 提取质量良好，部分需要复核")
else:
    print("\n❌ 提取质量一般，建议人工审核")

# 6. OCR 建议
print("\n【OCR 使用建议】")
print("-"*70)
print("如果 PDF 是扫描件或文本质量差，可以安装 OCR 支持:")
print("  pip install pytesseract pdf2image")
print("\n然后在代码中设置 use_ocr=True")

print("\n" + "="*70)
print("演示完成！")
print("="*70)
