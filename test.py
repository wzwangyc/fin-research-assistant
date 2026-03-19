#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试脚本 - 增强版"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.app.nlp.parser import PDFParser
from backend.app.nlp.ner import NERExtractor
from backend.app.nlp.sentiment import SentimentAnalyzer
from backend.app.sql.etl import ResearchETL


def test_pdf_parser():
    """测试 PDF 解析"""
    print("\n" + "="*60)
    print("测试 PDF 解析")
    print("="*60)
    parser = PDFParser()
    
    test_pdf = "data/raw/test.pdf"
    if Path(test_pdf).exists():
        result = parser.parse(test_pdf)
        print(f"✅ 标题：{result['title']}")
        print(f"✅ 页数：{result['page_count']}")
        print(f"✅ 内容长度：{len(result['content'])}")
        print(f"✅ 元数据：{result['metadata']}")
        print(f"✅ 表格数量：{len(result['tables'])}")
        return result
    else:
        print(f"❌ 测试文件不存在：{test_pdf}")
        return None


def test_ner(pdf_result):
    """测试实体识别"""
    print("\n" + "="*60)
    print("测试实体识别")
    print("="*60)
    ner = NERExtractor()
    
    if pdf_result and pdf_result.get('content'):
        # 只取前 5000 字测试
        text = pdf_result['content'][:5000]
        entities = ner.extract(text)
        
        print(f"\n📊 识别结果:")
        print(f"  股票代码：{[c[0] for c in entities['stock_codes']]}")
        print(f"  公司名称：{entities['companies'][:5]}")  # 只显示前 5 个
        print(f"  百分比：{entities['percentages'][:5]}")
        print(f"  日期：{entities['dates'][:3]}")
        
        # 验证
        if entities['stock_codes']:
            print("\n✅ 股票代码识别成功！")
        else:
            print("\n❌ 未识别到股票代码")
            
        if entities['companies']:
            print("✅ 公司名称识别成功！")
        else:
            print("❌ 未识别到公司名称")
        
        return entities
    return None


def test_sentiment():
    """测试情感分析"""
    print("\n" + "="*60)
    print("测试情感分析")
    print("="*60)
    sentiment = SentimentAnalyzer()
    
    test_texts = [
        "公司业绩强劲增长，盈利能力超预期，看好长期价值。",
        "业绩下滑，经营风险加大，建议谨慎。",
        "基本面稳定，维持中性评级。"
    ]
    
    for text in test_texts:
        result = sentiment.analyze(text)
        print(f"\n文本：{text}")
        print(f"情感：{result['label']} ({result['score']:.2f})")


def test_etl(pdf_result, entities):
    """测试 ETL 流程"""
    print("\n" + "="*60)
    print("测试 ETL 流程")
    print("="*60)
    
    etl = ResearchETL()
    
    # 初始化数据库
    try:
        etl.db.init_db("database/schema_sqlite.sql")
        print("✅ 数据库初始化成功")
    except Exception as e:
        print(f"⚠️ 数据库初始化警告：{e}")
    
    # 如果有 PDF 解析结果和实体，尝试入库
    if pdf_result and entities:
        print(f"\n📄 文档信息:")
        print(f"  标题：{pdf_result.get('title', 'N/A')}")
        print(f"  股票代码：{[c[0] for c in entities.get('stock_codes', [])]}")
        print(f"  公司名称：{entities.get('companies', [])[:3]}")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("金融研报助手 - 增强版功能测试")
    print("="*60)
    
    # 1. PDF 解析
    pdf_result = test_pdf_parser()
    
    # 2. 实体识别
    entities = test_ner(pdf_result)
    
    # 3. 情感分析
    test_sentiment()
    
    # 4. ETL 流程
    test_etl(pdf_result, entities)
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60)


if __name__ == "__main__":
    main()
