#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
金融研报助手 - 反幻觉增强版测试
核心原则：拒绝幻觉，只输出有依据的信息
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from backend.app.nlp.parser import PDFParser
from backend.app.nlp.ner import NERExtractor
from backend.app.nlp.anti_hallucination import AntiHallucinationChecker, ConfidenceLevel


def test_with_anti_hallucination(pdf_path: str):
    """带反幻觉检查的完整测试"""
    
    print("\n" + "="*70)
    print("金融研报助手 - 反幻觉增强版测试")
    print("="*70)
    print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试文件：{pdf_path}")
    print("="*70)
    
    # 1. PDF 解析
    print("\n【1/4】PDF 解析")
    print("-"*70)
    parser = PDFParser()
    pdf_result = parser.parse(pdf_path)
    
    if 'error' in pdf_result:
        print(f"❌ PDF 解析失败：{pdf_result['error']}")
        return
    
    print(f"✅ 标题：{pdf_result.get('title', 'N/A')}")
    print(f"✅ 页数：{pdf_result['page_count']}")
    print(f"✅ 内容长度：{len(pdf_result['content'])}")
    print(f"✅ 元数据：{pdf_result.get('metadata', {})}")
    print(f"✅ 表格数量：{len(pdf_result.get('tables', []))}")
    
    # 2. 基础 NER 提取
    print("\n【2/4】基础实体识别")
    print("-"*70)
    ner = NERExtractor()
    ner_result = ner.extract(pdf_result['content'][:10000])  # 只处理前 10000 字
    
    print(f"股票代码：{[c[0] for c in ner_result['stock_codes']]}")
    print(f"公司名称：{ner_result['companies'][:5]}")
    print(f"百分比：{ner_result['percentages'][:5]}")
    print(f"日期：{ner_result['dates'][:3]}")
    
    # 3. 反幻觉检查
    print("\n【3/4】反幻觉检查")
    print("-"*70)
    checker = AntiHallucinationChecker()
    
    all_entities = []
    for i, page in enumerate(pdf_result['content'].split('\n')[:10]):  # 检查前 10 页
        entities = checker.extract_with_evidence(page, page=i+1)
        all_entities.extend(entities)
    
    # 交叉验证
    all_entities = checker.cross_validate(all_entities)
    report = checker.generate_report(all_entities)
    
    print(f"\n📊 反幻觉统计:")
    print(f"  总实体数：{report['total_entities']}")
    print(f"  高置信度：{report['high_confidence']} ✅")
    print(f"  中置信度：{report['medium_confidence']} ⚠️")
    print(f"  低置信度：{report['low_confidence']} ❌")
    print(f"  未知/需复核：{report['unknown']} 🔄")
    print(f"  已交叉验证：{report['cross_validated']} ✅")
    
    # 4. 生成报告
    print("\n【4/4】生成可信度报告")
    print("-"*70)
    
    final_report = {
        'timestamp': datetime.now().isoformat(),
        'file': pdf_path,
        'document_info': {
            'title': pdf_result.get('title', 'N/A'),
            'page_count': pdf_result['page_count'],
            'metadata': pdf_result.get('metadata', {})
        },
        'extraction_quality': {
            'total_entities': report['total_entities'],
            'high_confidence_ratio': report['high_confidence'] / max(report['total_entities'], 1),
            'needs_review_count': len(report['needs_review']),
            'cross_validated_ratio': report['cross_validated'] / max(report['total_entities'], 1)
        },
        'entities': report['entities_by_type'],
        'hallucination_risk': 'LOW' if report['low_confidence'] == 0 else 
                             ('MEDIUM' if report['low_confidence'] < 3 else 'HIGH')
    }
    
    # 输出最终报告
    print("\n" + "="*70)
    print("最终可信度报告")
    print("="*70)
    print(f"幻觉风险等级：{final_report['hallucination_risk']}")
    print(f"高置信度比例：{final_report['extraction_quality']['high_confidence_ratio']:.1%}")
    print(f"需要人工复核：{final_report['extraction_quality']['needs_review_count']} 项")
    
    if final_report['hallucination_risk'] == 'LOW':
        print("\n✅ 报告质量良好，可以安全使用")
    elif final_report['hallucination_risk'] == 'MEDIUM':
        print("\n⚠️ 部分信息需要人工复核")
    else:
        print("\n❌ 幻觉风险较高，建议人工审核")
    
    if report['needs_review']:
        print("\n🔄 需要复核的实体:")
        for entity in report['needs_review'][:5]:
            print(f"  - {entity.value} ({entity.entity_type})")
            for ev in entity.evidence:
                print(f"    来源：第{ev.page}页")
                print(f"    原文：{ev.text[:80]}...")
    
    print("\n" + "="*70)
    print("✅ 测试完成！")
    print("="*70)
    
    return final_report


if __name__ == '__main__':
    test_with_anti_hallucination('data/raw/test.pdf')
