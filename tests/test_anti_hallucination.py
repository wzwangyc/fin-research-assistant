#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试反幻觉模块"""
import sys
sys.path.insert(0, '.')

from backend.app.nlp.anti_hallucination import AntiHallucinationChecker

checker = AntiHallucinationChecker()

# 测试用例
test_cases = [
    {
        'name': '正常研报内容',
        'text': """
        北方稀土 (600111) 发布 2021 年年报，实现营业收入 297.78 亿元，
        同比增长 40.2%。公司是全球最大的轻稀土供应商。
        包钢股份 (600010) 为其控股股东。
        """,
        'page': 1
    },
    {
        'name': '包含不确定信息',
        'text': """
        某公司可能实现收入 100 亿元（未经证实），
        股票代码可能是 123456（无效代码）。
        """,
        'page': 2
    },
    {
        'name': '需要交叉验证',
        'text': """
        北方稀土 (600111) 2021 年营收 297.78 亿元。
        另据公告，北方稀土 2021 年营业收入为 297.78 亿元。
        """,
        'page': 3
    }
]

print("="*60)
print("反幻觉模块测试")
print("="*60)

for i, case in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"测试 {i}: {case['name']}")
    print(f"{'='*60}")
    
    entities = checker.extract_with_evidence(case['text'], case['page'])
    entities = checker.cross_validate(entities)
    report = checker.generate_report(entities)
    
    print(f"\n📊 统计:")
    print(f"  总实体数：{report['total_entities']}")
    print(f"  高置信度：{report['high_confidence']} ✅")
    print(f"  中置信度：{report['medium_confidence']} ⚠️")
    print(f"  低置信度：{report['low_confidence']} ❌")
    print(f"  需要复核：{len(report['needs_review'])} 🔄")
    print(f"  已交叉验证：{report['cross_validated']} ✅")
    
    if report['needs_review']:
        print(f"\n⚠️ 需要人工复核的实体:")
        for entity in report['needs_review']:
            print(f"  - {entity['value']} ({entity['entity_type']})")
    
    print(f"\n📋 实体详情:")
    for entity_type, type_entities in report['entities_by_type'].items():
        print(f"\n  {entity_type}:")
        for entity in type_entities:
            review_flag = "🔄" if entity['needs_review'] else "✅"
            cross_flag = "✅" if entity['cross_validated'] else "⚠️"
            print(f"    {review_flag}{cross_flag} {entity['value']} "
                  f"(置信度：{entity['confidence']})")

print("\n" + "="*60)
print("✅ 反幻觉测试完成！")
print("="*60)
